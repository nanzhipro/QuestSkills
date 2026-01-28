import sys
import os

# Add parent directory to sys.path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.downloader import Downloader
from utils.parser import Parser
from utils.flomo import FlomoPusher

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 main.py <url> [flomo_api_url] [summary_content]")
        sys.exit(1)
        
    url = sys.argv[1]
    flomo_url = sys.argv[2] if len(sys.argv) > 2 else None
    summary_to_push = sys.argv[3] if len(sys.argv) > 3 else None

    downloader = Downloader()
    parser = Parser()
    
    html_data = downloader.fetch_html(url)
    if not html_data:
        print("Failed to fetch article.")
        sys.exit(1)
        
    title, author, publish_date = parser.extract_metadata(html_data)
    
    if parser.is_picture_page(html_data):
        content = parser.parse_picture_page(html_data, downloader)
    else:
        content = parser.parse_standard_article(html_data, downloader)
        
    print(f"TITLE: {title}")
    print(f"AUTHOR: {author}")
    print(f"PUBLISH_DATE: {publish_date}")
    print("-" * 20)
    print(content)

    # Handle flomo push
    if flomo_url and summary_to_push:
        pusher = FlomoPusher(flomo_url)
        success, msg = pusher.push(summary_to_push)
        if success:
            print(f"\n[flomo] Push successful: {msg}")
        else:
            print(f"\n[flomo] Push failed: {msg}")

if __name__ == "__main__":
    main()
