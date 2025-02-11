# c2cscrape.py
# This script scrapes the zfirelight blog for old episodes of coast to coast am and serves the audio/video as an rss feed for pocketcasts

import requests
from bs4 import BeautifulSoup
from typing import Optional

class C2CScrape:
    def __init__(self):
        self.url = 'https://zfirelight.blogspot.com/'
        self.episodes = []
        self.last_download = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def get_drive_link(self, url: str) -> Optional[str]:
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            iframes = soup.find_all('iframe')
            for iframe in iframes:
                src = iframe.get('src')
                if src and 'drive.google.com' in src:
                    print('Found drive link:', src)
                    return src
        except requests.RequestException as e:
            print(f'Error fetching page: {e}')
        return None

    def create_download_link(self) -> Optional[str]:
        url = self.get_drive_link(self.url)
        if not url:
            return None
            
        print('Creating download link for:', url)
        try:
            cleaned_url = url.split('/file/d/')[1].split('/')[0]
            download_link = f'https://drive.google.com/uc?export=download&id={cleaned_url}'
            print('Download link:', download_link)
            return download_link
        except IndexError:
            print('Error: Invalid URL format')
            return None

if __name__ == '__main__':
    c2c = C2CScrape()
    c2c.create_download_link()
