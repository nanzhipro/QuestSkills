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
        title_match = re.search(r'window\.msg_title = window\.title = [\'"](.*?)[\'"]', html_data)
        if not title_match:
            title_match = re.search(r'var msg_title = [\'"](.*?)[\'"]', html_data)
        if title_match:
            title = Parser.clean_text(title_match.group(1))
        
        # Author
        author = "Unknown"
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
        return "item_show_type: '8'" in html_data

    @staticmethod
    def parse_picture_page(html_data, downloader):
        pics = []
        pic_list_match = re.search(r'picture_page_info_list: \[(.*?)\]\s*,\s*reward_author_head', html_data, re.S)
        if pic_list_match:
            pic_block = pic_list_match.group(1)
            urls = re.findall(r'cdn_url: JsDecode\([\'"](.*?)[\'"]\)', pic_block)
            for url in urls:
                url = url.replace('\\x22', '"').replace('\\x26amp;', '&')
                pics.append(url)
        
        desc = ""
        desc_match = re.search(r'window\.desc = "(.*?)";', html_data, re.S)
        if desc_match:
            desc = desc_match.group(1).split('".replace')[0]
            desc = Parser.clean_text(desc)

        content_parts = []
        for pic_url in pics:
            local_path = downloader.download_image(pic_url)
            if local_path:
                content_parts.append(f"![image]({local_path})")
        
        content_parts.append(desc)
        return '\n\n'.join(content_parts).strip()

    @staticmethod
    def parse_standard_article(html_data, downloader):
        start_idx = html_data.find('id="js_content"')
        if start_idx == -1:
            return "Content container (js_content) not found."

        tag_start = html_data.rfind('<div', 0, start_idx)
        content_area = html_data[tag_start:]
        
        # Find end of content
        end_patterns = [r'id="qr_code"', r'id="js_pc_qr_code"', r'id="js_view_source"', r'<(script|style)']
        end_idx = len(content_area)
        for pattern in end_patterns:
            m = re.search(pattern, content_area)
            if m and m.start() < end_idx:
                end_idx = m.start()
        
        content_html = content_area[:end_idx]
        
        # Image Handling
        img_matches = list(re.finditer(r'<img[^>]+(?:data-src|src)=["\'](.*?)["\'][^>]*>', content_html))
        for m in reversed(img_matches):
            img_url = m.group(1)
            if not img_url.startswith('http'): continue
            local_path = downloader.download_image(img_url)
            if local_path:
                md_img = f"\n![image]({local_path})\n"
                content_html = content_html[:m.start()] + md_img + content_html[m.end():]

        # Structure Handling
        for i in range(1, 7):
            content_html = re.sub(f'<(h{i})[^>]*>(.*?)</h{i}>', rf'\n\n{"#"*i} \2\n\n', content_html, flags=re.S)
        
        content_html = re.sub(r'<(p|br|div|section|li|tr|blockquote)[^>]*>', '\n', content_html)
        
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
