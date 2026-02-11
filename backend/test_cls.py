
import requests
from bs4 import BeautifulSoup
import json
import re

def test_cls_scrape():
    url = "https://www.cls.cn/telegraph"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            print(f"Failed: {resp.status_code}")
            return

        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Method 1: Check for SSR Data
        script_tag = soup.find('script', id='__NEXT_DATA__')
        if script_tag:
            data = json.loads(script_tag.string)
            telegraph_list = data.get('props', {}).get('initialState', {}).get('telegraph', {}).get('telegraphList', [])
            print(f"Found {len(telegraph_list)} items via SSR JSON")
            if telegraph_list:
                print("First item:", telegraph_list[0].get('title', 'No Title'))
                return

        # Method 2: DOM Parsing (Fallback)
        # Scan for list items. Next.js often uses randomized classes, so exact classes might be brittle.
        # But usually content is readable.
        print("SSR JSON not found, checking text length:", len(resp.text))
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_cls_scrape()
