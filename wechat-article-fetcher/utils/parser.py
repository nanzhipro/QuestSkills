import re
import html

class Parser:
    @staticmethod
    def clean_text(text):
        if not text: return ""
        # Unescape common hex escapes found in WeChat JS variables
        text = re.sub(r'\\x([0-9a-fA-F]{2})', lambda m: chr(int(m.group(1), 16)), text)
        text = html.unescape(text)
        return text.strip()

    @staticmethod
    def extract_metadata(html_data):
        # Title
        title = "Unknown Title"
        # Try og:title first
        og_title = re.search(r'property="og:title" content="(.*?)"', html_data)
        if og_title:
            title = Parser.clean_text(og_title.group(1))
        else:
            title_match = re.search(r'window\.msg_title = window\.title = [\'"](.*?)[\'"]', html_data)
            if not title_match:
                title_match = re.search(r'var msg_title = [\'"](.*?)[\'"]', html_data)
            if title_match:
                title = Parser.clean_text(title_match.group(1))
        
        # Author
        author = "Unknown"
        # Try og:article:author
        og_author = re.search(r'property="og:article:author" content="(.*?)"', html_data)
        if og_author:
            author = Parser.clean_text(og_author.group(1))
        else:
            author_match = re.search(r'nickname: JsDecode\([\'"](.*?)[\'"]\)', html_data)
            if not author_match:
                author_match = re.search(r'var nickname = ["\'](.*?)["\'];', html_data)
            if author_match:
                author = Parser.clean_text(author_match.group(1))
            
        # Date
        publish_date = "Unknown"
        date_match = re.search(r'var (?:ct|create_time) = ["\'](\d+)["\']', html_data)
        if date_match:
            import datetime
            try:
                ts = int(date_match.group(1))
                publish_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass

        return title, author, publish_date

    @staticmethod
    def is_picture_page(html_data):
        # Flexible check for item_show_type: '8' or window.item_show_type = '8'
        return bool(re.search(r"item_show_type\s*[:=]\s*['\"]8['\"]", html_data))

    @staticmethod
    def parse_picture_page(html_data, downloader):
        pics = []
        # Find all cdn_url in the entire file if it's a picture page
        # This is more robust than trying to parse the exact JS block
        urls = re.findall(r'cdn_url\s*:\s*(?:JsDecode\()?[\'"](.*?)[\'"]', html_data)
        for url in urls:
            # Clean up WeChat escapes
            url = url.replace('\\x22', '"').replace('\\x26amp;', '&').replace('\\x26', '&')
            if url.startswith('//'): url = 'https:' + url
            if url not in pics:
                pics.append(url)
        
        # Fallback: if no pics found, look for og:image
        if not pics:
            og_img = re.search(r'property="og:image" content="(.*?)"', html_data)
            if og_img:
                pics.append(og_img.group(1))

        desc = ""
        # Try multiple ways to get description
        desc_match = re.search(r'window\.desc\s*=\s*"(.*?)";', html_data, re.S)
        if not desc_match:
            desc_match = re.search(r'var\s+msg_desc\s*=\s*["\'](.*?)["\'];', html_data, re.S)
        if not desc_match:
            desc_match = re.search(r'name="description"\s+content="(.*?)"', html_data, re.S)
            
        if desc_match:
            desc = desc_match.group(1).split('".replace')[0]
            # Clean up escapes like \x0a (newline)
            desc = desc.replace('\\x0a', '\n').replace('\\x26quot;', '"')
            desc = Parser.clean_text(desc)

        content_parts = []
        # Download images (limit to first 20 to avoid timeouts)
        for pic_url in pics[:20]:
            local_path = downloader.download_image(pic_url)
            if local_path:
                content_parts.append(f"![image]({local_path})")
        
        if desc:
            content_parts.append(desc)
            
        return '\n\n'.join(content_parts).strip()

    @staticmethod
    def parse_standard_article(html_data, downloader):
        # Flexible find for js_content
        # Sometimes it's id="js_content" or id='js_content' or even just id=js_content
        start_match = re.search(r'id=["\']?js_content["\']?', html_data)
        if not start_match:
            # Fallback to description if it's a very short article/post
            desc_match = re.search(r'name="description"\s+content="(.*?)"', html_data, re.S)
            if desc_match:
                content = desc_match.group(1).replace('\\x0a', '\n').replace('\\x26quot;', '"')
                return Parser.clean_text(content)
            return "Content container (js_content) not found."

        start_idx = start_match.start()
        tag_start = html_data.rfind('<div', 0, start_idx)
        if tag_start == -1: tag_start = start_idx
        
        content_area = html_data[tag_start:]
        
        # Find end of content
        end_patterns = [r'id="qr_code"', r'id="js_pc_qr_code"', r'id="js_view_source"', r'<(script|style)']
        end_idx = len(content_area)
        for pattern in end_patterns:
            m = re.search(pattern, content_area)
            if m and m.start() < end_idx:
                end_idx = m.start()
        
        content_html = content_area[:end_idx]
        
        # 1. Background Images (common for posters/headers)
        bg_matches = list(re.finditer(r'background-image:\s*url\([\'"]?(.*?)[\'"]?\)', content_html, re.I))
        for m in reversed(bg_matches):
            bg_url = m.group(1)
            if bg_url.startswith('//'): bg_url = 'https:' + bg_url
            if not bg_url.startswith('http'): continue
            local_path = downloader.download_image(bg_url)
            if local_path:
                md_img = f"\n![image]({local_path})\n"
                content_html = content_html[:m.start()] + md_img + content_html[m.end():]

        # 2. Standard <img> tags
        img_matches = list(re.finditer(r'<img[^>]+(?:data-src|src)=["\'](.*?)["\'][^>]*>', content_html, re.S | re.I))
        for m in reversed(img_matches):
            img_url = m.group(1)
            if img_url.startswith('//'): img_url = 'https:' + img_url
            if not img_url.startswith('http'): continue
            local_path = downloader.download_image(img_url)
            if local_path:
                md_img = f"\n![image]({local_path})\n"
                content_html = content_html[:m.start()] + md_img + content_html[m.end():]

        # Structure Handling
        for i in range(1, 7):
            content_html = re.sub(f'<(h{i})[^>]*>(.*?)</h{i}>', rf'\n\n{"#"*i} \2\n\n', content_html, flags=re.S | re.I)
        
        content_html = re.sub(r'<(p|br|div|section|li|tr|blockquote)[^>]*>', '\n', content_html, flags=re.I)
        
        clean_body = re.sub(r'<[^>]+>', '', content_html)
        clean_body = html.unescape(clean_body)
        
        lines = [line.strip() for line in clean_body.split('\n')]
        final_lines = []
        prev_empty = False
        for line in lines:
            if line:
                final_lines.append(line)
                prev_empty = False
            elif not prev_empty:
                final_lines.append("")
                prev_empty = True
        
        return '\n'.join(final_lines).strip()
