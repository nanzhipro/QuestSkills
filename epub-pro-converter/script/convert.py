import os
import sys
import shutil
import logging
from ebooklib import epub
from bs4 import BeautifulSoup
from xhtml2pdf import pisa
import markdown
from pypdf import PdfReader

# Configuration
WORK_DIR = "work"

# Setup Logging (Console only)
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def log_error(msg, e=None):
    if e:
        logging.error(f"{msg}: {str(e)}")
    else:
        logging.error(msg)

def extract_epub(epub_path, work_dir):
    logging.info(f"Extracting EPUB: {epub_path}")
    book = epub.read_epub(epub_path)
    
    html_content = []
    images_dir = os.path.join(work_dir, "images")
    fonts_dir = os.path.join(work_dir, "fonts")
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(fonts_dir, exist_ok=True)
    
    # Sort items by order in spine
    spine_ids = [item[0] for item in book.spine]
    items = list(book.get_items())
    
    # Map item ID to item
    item_map = {item.id: item for item in items}
    
    # Process spine items (HTML)
    for s_id in spine_ids:
        item = item_map.get(s_id)
        if item and isinstance(item, epub.EpubHtml):
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            # Extract body content
            body = soup.find('body')
            if body:
                html_content.append(str(body))
            else:
                html_content.append(str(soup))
                
    # Extract images and cover
    for item in items:
        if isinstance(item, (epub.EpubImage, epub.EpubCover)):
            img_name = os.path.basename(item.get_name())
            img_path = os.path.join(images_dir, img_name)
            with open(img_path, 'wb') as f:
                f.write(item.get_content())
            logging.info(f"Extracted image: {img_path} (Type: {type(item).__name__})")
        
        # Extract fonts
        if 'font' in item.get_name().lower():
            font_name = os.path.basename(item.get_name())
            font_path = os.path.join(fonts_dir, font_name)
            with open(font_path, 'wb') as f:
                f.write(item.get_content())
            logging.info(f"Extracted font: {font_path}")
            
    return "".join(html_content), book.get_metadata('DC', 'title')[0][0] if book.get_metadata('DC', 'title') else "Untitled"

def process_html(raw_html, title, fonts_dir):
    logging.info("Processing HTML for PDF/MD")
    soup = BeautifulSoup(raw_html, 'html.parser')
    
    # Fix image paths
    for img in soup.find_all('img'):
        src = img.get('src', '')
        if src:
            img['src'] = os.path.abspath(os.path.join(os.path.dirname(fonts_dir), "images", os.path.basename(src)))
            
    # Dynamic Font definitions
    font_css = ""
    extracted_fonts = os.listdir(fonts_dir) if os.path.exists(fonts_dir) else []
    
    # Try to map fonts automatically
    serif_font = "serif"
    heading_font = "sans-serif"
    
    if extracted_fonts:
        for font_file in extracted_fonts:
            font_path = os.path.join(fonts_dir, font_file)
            font_name = os.path.splitext(font_file)[0]
            
            # Simple heuristic for font-face
            style = "normal"
            weight = "normal"
            if "italic" in font_file.lower(): style = "italic"
            if "bold" in font_file.lower(): weight = "bold"
            
            # Create a generic font-family name based on file name prefix (before - or space)
            family_base = font_name.split('-')[0].split(' ')[0]
            
            font_css += f"""
            @font-face {{
                font-family: '{family_base}';
                src: url('{font_path}');
                font-style: {style};
                font-weight: {weight};
            }}
            """
            # Assign first found fonts as defaults
            if serif_font == "serif" and "regular" in font_file.lower():
                serif_font = f"'{family_base}'"
            if heading_font == "sans-serif" and ("bold" in font_file.lower() or "display" in font_file.lower()):
                heading_font = f"'{family_base}'"

    # Add CSS for PDF (Optimized for Publishing-grade Reading Experience)
    style = font_css + f"""
    @page {{
        size: A4;
        margin: 2.5cm;
        @frame footer {{
            -pdf-frame-content: footerContent;
            bottom: 1.5cm;
            margin-left: 2.5cm;
            margin-right: 2.5cm;
            height: 1cm;
        }}
    }}
    body {{
        font-family: {serif_font}, serif;
        line-height: 1.5em;
        font-size: 13pt;
        text-align: justify;
        color: #1a1a1a;
    }}
    h1 {{
        font-family: {heading_font}, sans-serif;
        font-size: 26pt;
        text-align: center;
        margin-top: 2em;
        margin-bottom: 1em;
        color: #000;
        page-break-before: always;
    }}
    h2 {{
        font-family: {heading_font}, sans-serif;
        font-size: 20pt;
        margin-top: 1.5em;
        margin-bottom: 0.8em;
        color: #333;
        border-bottom: 0.5pt solid #eee;
        padding-bottom: 0.2em;
    }}
    h3 {{
        font-family: {heading_font}, sans-serif;
        font-size: 16pt;
        margin-top: 1.2em;
        margin-bottom: 0.6em;
        color: #444;
    }}
    p {{
        text-indent: 2em;
        margin-bottom: 0.8em;
    }}
    img {{
        max-width: 100%;
        height: auto;
        display: block;
        margin: 1.5em auto;
    }}
    blockquote {{
        margin: 1.5em 2em;
        font-style: italic;
        color: #555;
        border-left: 2pt solid #ddd;
        padding-left: 1em;
    }}
    #footerContent {{
        text-align: center;
        font-size: 10pt;
        color: #888;
    }}
    """
    
    full_html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{title}</title>
        <style>{style}</style>
    </head>
    <body>
        <div id="footerContent">
            <pdf:pagenumber>
        </div>
        <h1>{title}</h1>
        {str(soup)}
    </body>
    </html>
    """
    return full_html

def convert_to_pdf(html_content, output_path):
    logging.info(f"Generating PDF: {output_path}")
    with open(output_path, "wb") as f:
        pisa_status = pisa.CreatePDF(html_content, dest=f)
    
    if pisa_status.err:
        log_error(f"PDF generation failed: {pisa_status.err}")
        return False
    return True

from markdownify import markdownify as md
import re

def convert_to_md(html_content, output_path, work_dir):
    logging.info(f"Generating Markdown: {output_path}")
    
    # Use markdownify for robust conversion
    md_text = md(html_content, heading_style="ATX")
    
    # Clean up multiple newlines
    md_text = re.sub(r'\n{3,}', '\n\n', md_text)
    
    # Fix image paths for MD
    md_images_dir = os.path.join(os.path.dirname(output_path), "images")
    os.makedirs(md_images_dir, exist_ok=True)
    
    work_images_dir = os.path.join(work_dir, "images")
    if os.path.exists(work_images_dir):
        for img_file in os.listdir(work_images_dir):
            shutil.copy2(os.path.join(work_images_dir, img_file), os.path.join(md_images_dir, img_file))
        
    abs_work_images_path = os.path.abspath(work_images_dir)
    md_text = md_text.replace(abs_work_images_path, "images")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md_text)
    return True

def validate_pdf(pdf_path):
    logging.info(f"Validating PDF: {pdf_path}")
    try:
        reader = PdfReader(pdf_path)
        pages = len(reader.pages)
        logging.info(f"PDF has {pages} pages")
        if pages == 0:
            return False
        return True
    except Exception as e:
        log_error("PDF validation failed", e)
        return False

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Convert EPUB to PDF and Markdown")
    parser.add_argument("input", nargs="?", help="Path to input EPUB file")
    args = parser.parse_args()

    epub_path_input = args.input
    
    # If not provided via CLI, ask the user
    if not epub_path_input:
        try:
            epub_path_input = input("Please enter the path to the EPUB file (or press Enter to exit): ").strip()
        except EOFError:
            pass
            
    if not epub_path_input:
        print("No input file provided. Terminating process.")
        sys.exit(0)

    epub_path = os.path.abspath(epub_path_input)
    if not os.path.exists(epub_path):
        log_error(f"Input file not found: {epub_path}")
        sys.exit(1)

    output_pdf = epub_path + ".pdf"
    output_md = epub_path + ".md"
    
    # Use unique work dir per file to avoid collision
    # Use hash of filename to avoid long paths and special character issues in CSS
    import hashlib
    file_hash = hashlib.md5(os.path.basename(epub_path).encode()).hexdigest()[:10]
    file_slug = f"{os.path.basename(epub_path)[:20].replace(' ', '_')}_{file_hash}"
    current_work_dir = os.path.join(WORK_DIR, file_slug)
    os.makedirs(current_work_dir, exist_ok=True)

    try:
        # Backup
        bak_path = epub_path + ".bak"
        if not os.path.exists(bak_path):
            shutil.copy2(epub_path, bak_path)
            logging.info(f"Created backup: {bak_path}")

        # Step 1: Extract
        html_raw, title = extract_epub(epub_path, current_work_dir)
        
        # Step 2: Process
        fonts_dir = os.path.join(current_work_dir, "fonts")
        html_final = process_html(html_raw, title, fonts_dir)
        
        # Step 3: Convert to PDF
        success_pdf = convert_to_pdf(html_final, output_pdf)
        if success_pdf:
            validate_pdf(output_pdf)
        
        # Step 4: Convert to MD
        convert_to_md(html_final, output_md, current_work_dir)
        
        logging.info(f"Markdown generated at: {output_md}. AI Agent will now proceed with Core Content Extraction.")
        
        logging.info("Conversion tasks completed successfully")
        
    except Exception as e:
        log_error("Main process failed", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
