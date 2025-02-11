import requests
from bs4 import BeautifulSoup
import datetime
import os
import re

class C2CScrape:
    def __init__(self):
        self.url = 'https://zfirelight.blogspot.com/'
        self.episodes = []
        self.last_download = None
        self.last_download_link = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def sanitize_filename(self, filename):
        # Remove or replace invalid filename characters
        return re.sub(r'[<>:"/\\|?*]', '-', filename)

    def get_drive_link(self, url):
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            self.soup = BeautifulSoup(response.text, 'html.parser')
            
            iframes = self.soup.find_all('iframe')
            for iframe in iframes:
                src = iframe.get('src')
                if src and 'drive.google.com' in src:
                    print('Found drive link:', src)
                    return src
        except requests.RequestException as e:
            print(f'Error fetching page: {e}')
        return None

    def get_episode_info(self, soup):
        title_element = soup.find('h3', class_='post-title entry-title')
        if not title_element:
            return None
            
        title_link = title_element.find('a')
        if not title_link:
            return None
            
        full_title = title_link.text
        date_str = full_title.split(' ')[0]
        
        return {
            'title': full_title,
            'date': date_str,
            'url': title_link['href']
        }

    def create_download_link(self):
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

    def download_episode(self, url):
        try:
            episode_data = self.get_episode_info(self.soup)
            if not episode_data:
                print('Error: Could not get episode info')
                return

            # Create downloads directory if it doesn't exist
            download_dir = 'downloads'
            os.makedirs(download_dir, exist_ok=True)

            # Get current date
            date = datetime.datetime.now().strftime('%Y-%m-%d')

            # Create sanitized filename
            filename = f'{episode_data["title"]} {date}.mp4'
            safe_filename = self.sanitize_filename(filename)
            filepath = os.path.join(download_dir, safe_filename)

            # Check if file already exists
            if os.path.exists(filepath):
                print(f'File already exists: {safe_filename}')
                return

            # Download the file
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
                
            with open(filepath, 'wb') as f:
                f.write(response.content)
                print(f'Downloaded: {safe_filename}')
            
            # Update last download info
            self.last_download = date
            self.last_download_link = url

        except requests.RequestException as e:
            print(f'Error downloading episode: {e}')
        except Exception as e:
            print(f'Error: {e}')


    def process_episode(self):
        drive_url = self.get_drive_link(self.url)
        if drive_url:
            download_url = self.create_download_link()
            if download_url:
                self.download_episode(download_url)

class createRss:
    def __init__(self):
        self.episodes = []
        self.feed = None
        self.feed_title = 'Coast to Coast AM'
        self.feed_link = 'https://zfirelight.blogspot.com/'
        self.feed_description = 'Coast to Coast AM episodes'

    def create_feed(self):
        self.feed = f'<?xml version="1.0" encoding="UTF-8"?>\n'
        self.feed += f'<rss version="2.0">\n'
        self.feed += f'<channel>\n'
        self.feed += f'<title>{self.feed_title}</title>\n'
        self.feed += f'<link>{self.feed_link}</link>\n'
        self.feed += f'<description>{self.feed_description}</description>\n'
        for episode in self.episodes:
            self.feed += f'<item>\n'
            self.feed += f'<title>{episode["title"]}</title>\n'
            self.feed += f'<link>{episode["url"]}</link>\n'
            self.feed += f'<description>{episode["date"]}</description>\n'
            self.feed += f'</item>\n'
        self.feed += f'</channel>\n'
        self.feed += f'</rss>\n'

    def save_feed(self):
        try:
            with open('feed.xml', 'w') as f:
                f.write(self.feed)
                print('Feed saved')
        except Exception as e:
            print(f'Error saving feed: {e}')

    def add_episode(self, episode):
        self.episodes.append(episode)

    def process_episodes(self):
        c2c = C2CScrape()
        response = requests.get(c2c.url, headers=c2c.headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        posts = soup.find_all('div', class_='post hentry')
        for post in posts:
            episode = c2c.get_episode_info(post)
            if episode:
                self.add_episode(episode)
        self.create_feed()
        self.save_feed()

if __name__ == '__main__':
    c2c = C2CScrape()
    c2c.process_episode()
    rss = createRss()
    rss.process_episodes()
