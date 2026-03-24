#!/usr/bin/env python3
"""
Scan extracted text for potential PII/sensitive information and output JSON report.
"""
import argparse
import json
import os
import re
import sys


def _load_segments(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    stripped = content.lstrip()
    if not stripped:
        return []
    first = stripped[0]
    if first == "{":
        # JSONL or single JSON object
        segments = []
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict) and "text" in obj:
                    segments.append(obj)
            except json.JSONDecodeError:
                continue
        if segments:
            return segments
        try:
            obj = json.loads(content)
            if isinstance(obj, dict):
                if "segments" in obj and isinstance(obj["segments"], list):
                    return obj["segments"]
            if isinstance(obj, list):
                return obj
        except Exception:
            pass
    if first == "[":
        try:
            obj = json.loads(content)
            if isinstance(obj, list):
                return obj
        except Exception:
            pass

    # Fallback: plain text, split by lines
    segments = []
    for i, line in enumerate(content.splitlines(), start=1):
        if line.strip():
            segments.append({"type": "text", "location": f"line:{i}", "text": line})
    return segments


def _luhn_check(number):
    digits = [int(d) for d in re.sub(r"\D", "", number)]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


def _valid_ip(value):
    parts = value.split(".")
    if len(parts) != 4:
        return False
    for p in parts:
        try:
            n = int(p)
        except Exception:
            return False
        if n < 0 or n > 255:
            return False
    return True


def _valid_cn_id(value):
    value = value.upper()
    if not re.match(r"^\d{17}[0-9X]$", value):
        return False
    weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    check_map = "10X98765432"
    s = 0
    for i in range(17):
        s += int(value[i]) * weights[i]
    return check_map[s % 11] == value[-1]


def _digits_len(value):
    return len(re.sub(r"\D", "", value))


def _redact_keep_last(value, keep=2):
    digits = re.sub(r"\D", "", value)
    if len(digits) <= keep:
        return "*" * len(digits)
    return "*" * (len(digits) - keep) + digits[-keep:]


def _redact_email(value):
    parts = value.split("@")
    if len(parts) != 2:
        return "***"
    name, domain = parts
    if len(name) <= 1:
        masked = "*"
    else:
        masked = name[0] + "*" * (len(name) - 1)
    return f"{masked}@{domain}"


def _context(text, start, end, max_len):
    half = max_len // 2
    left = max(0, start - half)
    right = min(len(text), end + half)
    snippet = text[left:right].replace("\n", " ")
    return snippet.strip()


def _pattern_list():
    return [
        {
            "type": "email",
            "regex": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
            "confidence": 0.9,
            "redact": _redact_email,
        },
        {
            "type": "phone",
            "regex": re.compile(r"\b1[3-9]\d{9}\b"),
            "confidence": 0.85,
            "redact": lambda v: _redact_keep_last(v, 2),
        },
        {
            "type": "phone",
            "regex": re.compile(r"\b\+?\d[\d\-\s]{6,}\d\b"),
            "confidence": 0.4,
            "validator": lambda v: 7 <= _digits_len(v) <= 15,
            "redact": lambda v: _redact_keep_last(v, 2),
        },
        {
            "type": "id_cn",
            "regex": re.compile(r"\b\d{17}[0-9Xx]\b"),
            "confidence": 0.95,
            "validator": _valid_cn_id,
            "redact": lambda v: _redact_keep_last(v, 2),
        },
        {
            "type": "ssn_us",
            "regex": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
            "confidence": 0.9,
            "redact": lambda v: "***-**-" + v[-4:],
        },
        {
            "type": "credit_card",
            "regex": re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
            "confidence": 0.8,
            "validator": _luhn_check,
            "redact": lambda v: "**** **** **** " + re.sub(r"\D", "", v)[-4:],
        },
        {
            "type": "bank_account",
            "regex": re.compile(r"(?:账号|账户|account|acct)[:：\s]*([0-9]{8,20})"),
            "value_group": 1,
            "confidence": 0.7,
            "redact": lambda v: _redact_keep_last(v, 4),
        },
        {
            "type": "ip_address",
            "regex": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
            "confidence": 0.5,
            "validator": _valid_ip,
            "redact": lambda v: v,
        },
        {
            "type": "credential",
            "regex": re.compile(r"(?i)(password|pwd|pass|密码|口令)[:：\s]+([^\s,;]{4,})"),
            "value_group": 2,
            "confidence": 0.9,
            "redact": lambda v: "***",
        },
        {
            "type": "api_key",
            "regex": re.compile(r"\bAKIA[0-9A-Z]{16}\b|\bsk-[A-Za-z0-9]{20,}\b"),
            "confidence": 0.95,
            "redact": lambda v: v[:4] + "***" + v[-4:],
        },
        {
            "type": "name",
            "regex": re.compile(r"(?:姓名|联系人|收件人)[:：\s]*([\u4e00-\u9fa5]{2,4})"),
            "value_group": 1,
            "confidence": 0.4,
            "redact": lambda v: v[0] + "*" * (len(v) - 1),
        },
        {
            "type": "address",
            "regex": re.compile(r"(?:地址|住址|邮寄地址)[:：\s]*([^\n,;]{6,60})"),
            "value_group": 1,
            "confidence": 0.4,
            "redact": lambda v: v[:2] + "***",
        },
    ]


def _risk_level(item_type):
    high = {"id_cn", "ssn_us", "credit_card", "credential", "api_key"}
    medium = {"phone", "email", "bank_account"}
    if item_type in high:
        return "high"
    if item_type in medium:
        return "medium"
    return "low"


def scan_segments(segments, max_context=120, min_confidence=0.0):
    patterns = _pattern_list()
    findings = []
    seen = set()
    for seg in segments:
        text = seg.get("text", "") or ""
        if not text:
            continue
        for pat in patterns:
            regex = pat["regex"]
            for match in regex.finditer(text):
                value = match.group(pat.get("value_group", 0))
                if not value:
                    continue
                if "validator" in pat and pat["validator"] is not None:
                    try:
                        if not pat["validator"](value):
                            continue
                    except Exception:
                        continue
                confidence = pat.get("confidence", 0.5)
                if confidence < min_confidence:
                    continue
                location = seg.get("location", "")
                key = (pat["type"], value, location)
                if key in seen:
                    continue
                seen.add(key)
                redacted = pat.get("redact", lambda v: "***")(value)
                findings.append({
                    "type": pat["type"],
                    "value": value,
                    "redacted": redacted,
                    "location": location,
                    "risk": _risk_level(pat["type"]),
                    "confidence": confidence,
                    "context": _context(text, match.start(), match.end(), max_context),
                })
    return findings


def summarize(findings):
    by_type = {}
    for f in findings:
        by_type[f["type"]] = by_type.get(f["type"], 0) + 1
    return {
        "total_matches": len(findings),
        "by_type": by_type,
    }


def main():
    parser = argparse.ArgumentParser(description="Scan text for PII/sensitive info and output JSON report.")
    parser.add_argument("--input", required=True, help="Input JSONL or text file")
    parser.add_argument("--output", required=True, help="Output JSON file")
    parser.add_argument("--max-context", type=int, default=120, help="Max context length")
    parser.add_argument("--min-confidence", type=float, default=0.0, help="Minimum confidence threshold")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        sys.stderr.write(f"Input file not found: {args.input}\n")
        sys.exit(1)

    segments = _load_segments(args.input)
    findings = scan_segments(segments, max_context=args.max_context, min_confidence=args.min_confidence)

    report = {
        "source": args.input,
        "summary": summarize(findings),
        "findings": findings,
    }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
