#!/usr/bin/env python3
"""
Extract text from PDF/DOCX/XLSX/PPTX into JSONL with location metadata.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from xml.etree import ElementTree as ET


def _optional_import(name):
    try:
        return __import__(name)
    except Exception:
        return None


def _detect_type(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in {".pdf", ".docx", ".xlsx", ".pptx"}:
        return ext[1:]
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as zf:
            names = set(zf.namelist())
        if "word/document.xml" in names:
            return "docx"
        if "ppt/presentation.xml" in names:
            return "pptx"
        if "xl/workbook.xml" in names:
            return "xlsx"
    return None


def _write_jsonl(segments, output_path):
    out = sys.stdout if output_path == "-" else open(output_path, "w", encoding="utf-8")
    try:
        for seg in segments:
            out.write(json.dumps(seg, ensure_ascii=False) + "\n")
    finally:
        if out is not sys.stdout:
            out.close()


def _pdf_text_pymupdf(path):
    fitz = _optional_import("fitz")
    if not fitz:
        return None
    doc = fitz.open(path)
    segments = []
    for i, page in enumerate(doc, start=1):
        text = page.get_text("text") or ""
        segments.append({"type": "pdf", "location": f"page:{i}", "text": text})
    return segments


def _pdf_text_pdfplumber(path):
    pdfplumber = _optional_import("pdfplumber")
    if not pdfplumber:
        return None
    segments = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            segments.append({"type": "pdf", "location": f"page:{i}", "text": text})
    return segments


def _pdf_text_pdftotext(path):
    if not shutil.which("pdftotext"):
        return None
    cmd = ["pdftotext", "-layout", path, "-"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        return None
    raw = proc.stdout
    pages = raw.split("\f")
    segments = []
    for i, page in enumerate(pages, start=1):
        text = page.strip("\n")
        segments.append({"type": "pdf", "location": f"page:{i}", "text": text})
    return segments


def extract_pdf(path):
    segments = _pdf_text_pymupdf(path)
    if segments is None:
        segments = _pdf_text_pdfplumber(path)
    if segments is None:
        segments = _pdf_text_pdftotext(path)
    if segments is None:
        raise RuntimeError("No PDF extractor available. Install pymupdf or pdfplumber, or ensure pdftotext exists.")
    return segments


def extract_docx(path):
    docx = _optional_import("docx")
    if docx:
        doc = docx.Document(path)
        segments = []
        for i, p in enumerate(doc.paragraphs, start=1):
            text = (p.text or "").strip()
            if text:
                segments.append({"type": "docx", "location": f"para:{i}", "text": text})
        for t_i, table in enumerate(doc.tables, start=1):
            for r_i, row in enumerate(table.rows, start=1):
                cells = [c.text.strip() for c in row.cells]
                if any(cells):
                    segments.append({"type": "docx", "location": f"table:{t_i} row:{r_i}", "text": " | ".join(cells)})
        return segments

    # Fallback: parse XML
    segments = []
    with zipfile.ZipFile(path) as zf:
        xml = zf.read("word/document.xml")
    root = ET.fromstring(xml)
    para_index = 0
    for p in root.iter():
        if p.tag.endswith("}p"):
            para_index += 1
            parts = []
            for t in p.iter():
                if t.tag.endswith("}t") and t.text:
                    parts.append(t.text)
            text = "".join(parts).strip()
            if text:
                segments.append({"type": "docx", "location": f"para:{para_index}", "text": text})
    return segments


def extract_pptx(path):
    pptx = _optional_import("pptx")
    if pptx:
        prs = pptx.Presentation(path)
        segments = []
        for i, slide in enumerate(prs.slides, start=1):
            texts = []
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    t = shape.text
                    if t:
                        texts.append(t)
            text = "\n".join([t for t in texts if t.strip()])
            segments.append({"type": "pptx", "location": f"slide:{i}", "text": text})
        return segments

    segments = []
    with zipfile.ZipFile(path) as zf:
        slide_names = [n for n in zf.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml")]
        def _slide_num(name):
            m = re.search(r"slide(\d+)\.xml", name)
            return int(m.group(1)) if m else 0
        slide_names.sort(key=_slide_num)
        for i, name in enumerate(slide_names, start=1):
            xml = zf.read(name)
            root = ET.fromstring(xml)
            texts = [t.text for t in root.iter() if t.tag.endswith("}t") and t.text]
            text = " ".join(texts).strip()
            segments.append({"type": "pptx", "location": f"slide:{i}", "text": text})
    return segments


def extract_xlsx(path):
    openpyxl = _optional_import("openpyxl")
    if openpyxl:
        wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
        segments = []
        for ws in wb.worksheets:
            for row in ws.iter_rows():
                for cell in row:
                    if cell.value is None:
                        continue
                    text = str(cell.value)
                    if text.strip():
                        segments.append({"type": "xlsx", "location": f"sheet:{ws.title} cell:{cell.coordinate}", "text": text})
        return segments

    segments = []
    with zipfile.ZipFile(path) as zf:
        names = set(zf.namelist())
        shared = []
        if "xl/sharedStrings.xml" in names:
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for t in root.iter():
                if t.tag.endswith("}t"):
                    shared.append(t.text or "")
        sheet_names = [n for n in names if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")]
        def _sheet_num(name):
            m = re.search(r"sheet(\d+)\.xml", name)
            return int(m.group(1)) if m else 0
        sheet_names.sort(key=_sheet_num)
        for idx, name in enumerate(sheet_names, start=1):
            root = ET.fromstring(zf.read(name))
            for c in root.iter():
                if not c.tag.endswith("}c"):
                    continue
                ref = c.get("r") or ""
                cell_type = c.get("t")
                v = None
                for child in c:
                    if child.tag.endswith("}v"):
                        v = child.text or ""
                        break
                if v is None:
                    continue
                if cell_type == "s":
                    try:
                        v = shared[int(v)]
                    except Exception:
                        pass
                text = str(v).strip()
                if text:
                    segments.append({"type": "xlsx", "location": f"sheet:{idx} cell:{ref}", "text": text})
    return segments


def _warn_if_empty(segments):
    if not segments:
        return
    total = sum(len(seg.get("text", "")) for seg in segments)
    if total < 20:
        sys.stderr.write("[WARN] Extracted text is very small. The file may be scanned; consider OCR.\n")


def main():
    parser = argparse.ArgumentParser(description="Extract text from PDF/DOCX/XLSX/PPTX into JSONL.")
    parser.add_argument("--input", required=True, help="Input file path")
    parser.add_argument("--output", required=True, help="Output JSONL path or '-' for stdout")
    args = parser.parse_args()

    path = args.input
    if not os.path.exists(path):
        sys.stderr.write(f"Input file not found: {path}\n")
        sys.exit(1)

    doc_type = _detect_type(path)
    if not doc_type:
        sys.stderr.write("Unsupported file type. Use PDF/DOCX/XLSX/PPTX.\n")
        sys.exit(1)

    if doc_type == "pdf":
        segments = extract_pdf(path)
    elif doc_type == "docx":
        segments = extract_docx(path)
    elif doc_type == "pptx":
        segments = extract_pptx(path)
    elif doc_type == "xlsx":
        segments = extract_xlsx(path)
    else:
        sys.stderr.write("Unsupported file type.\n")
        sys.exit(1)

    for seg in segments:
        seg["source"] = path

    _warn_if_empty(segments)
    _write_jsonl(segments, args.output)


if __name__ == "__main__":
    main()
