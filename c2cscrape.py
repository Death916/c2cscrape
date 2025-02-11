#c2cscrape.py
# This script scrapes the zfirelight blog for old episodes of coast to coast am and serves the audio/video as an rss feed for pocketcasts

from playwright.sync_api import sync_playwright

class C2CScrape:
    def __init__(self):
        self.url = 'https://zfirelight.blogspot.com/'
        self.episodes = []
        playwright = sync_playwright().start()
        self.browser = playwright.chromium.launch(headless=True)
        self.page = self.browser.new_page()
        self.last_download= None

    def get_drive_link(self, url):
        self.page.goto(url)
        self.page.wait_for_load_state('networkidle')
        iframes = self.page.query_selector_all('iframe')
        for iframe in iframes:
            src = iframe.get_attribute('src')
            if src and 'drive.google.com' in src:
                print('Found drive link:', src)
                return src
        return None

    def close(self):
        if self.browser:
            self.browser.close()

    def create_download_link(self):
        url = self.get_drive_link(self.url)
        print('Creating download link for:', url)
        cleaned_url = url.split('/file/d/')[1].split('/')[0]
        download_link = f'https://drive.google.com/uc?export=download&id={cleaned_url}'
        print('Download link:', download_link)
        return download_link

if __name__ == '__main__':
    c2c = C2CScrape()
    try:
        c2c.create_download_link()
    finally:
        c2c.close()

