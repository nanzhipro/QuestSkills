import urllib.request
import hashlib
import os
import re

class Downloader:
    def __init__(self, user_agent=None):
        self.user_agent = user_agent or "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    def fetch_html(self, url):
        req = urllib.request.Request(url, headers={'User-Agent': self.user_agent})
        try:
            with urllib.request.urlopen(req) as response:
                return response.read().decode('utf-8')
        except Exception as e:
            print(f"Error fetching HTML from {url}: {e}")
            return None

    def download_image(self, url, folder='images'):
        if not url: return None
        if not os.path.exists(folder):
            os.makedirs(folder)
        
        url_hash = hashlib.md5(url.encode()).hexdigest()
        fmt_match = re.search(r'wx_fmt=([a-z]+)', url)
        ext = fmt_match.group(1) if fmt_match else 'jpg'
        
        filename = f"{url_hash}.{ext}"
        filepath = os.path.join(folder, filename)
        
        if not os.path.exists(filepath):
            try:
                req = urllib.request.Request(url, headers={'User-Agent': self.user_agent})
                with urllib.request.urlopen(req) as response:
                    with open(filepath, 'wb') as f:
                        f.write(response.read())
            except Exception:
                return None
        return filepath
