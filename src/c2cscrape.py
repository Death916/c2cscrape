import requests
from bs4 import BeautifulSoup
import datetime
import os
import re
import threading
import time
import random

class C2CScrape:
    def __init__(self):
        self.url = 'https://zfirelight.blogspot.com/'
        self.episodes = []
        self.last_download = None
        self.last_download_link = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.episodes_downloaded = 0
        self.download_location = '/downloads'
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
            download_dir = '/downloads'
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
            print('sleeping for 3-7 seconds')
            time.sleep(random.randint(3,7))
            
            # Update last download info
            self.episodes_downloaded += 1
            self.last_download = date
            self.last_download_link = url

        except requests.RequestException as e:
            print(f'Error downloading episode: {e}')
        except Exception as e:
            print(f'Error: {e}')

    def is_duplicate_file(self, soup):
        try:
            episode_data = self.get_episode_info(soup)
            if not episode_data:
                return False
                
            date = datetime.datetime.now().strftime('%Y-%m-%d')
            filename = f'{episode_data["title"]} {date}.mp4'
            safe_filename = self.sanitize_filename(filename)
            filepath = os.path.join('downloads', safe_filename)
            
            return os.path.exists(filepath)
            
        except Exception as e:
            print(f'Error checking duplicate: {e}')
            return False


    def process_episode(self):
        try:
            drive_url = self.get_drive_link(self.url)  # This sets self.soup
            if not drive_url:
                return
                
            if self.is_duplicate_file(self.soup):
                print('Episode already exists, skipping download')
                return

            download_url = self.create_download_link()
            if download_url:
                self.download_episode(download_url)
                
        except requests.RequestException as e:
            print(f'Error processing episode: {e}')
        except Exception as e:
            print(f'Error: {e}')
       



    # timer to check for new episodes every 12 hours
    def timer(self):
    
        try:
            # Run our core operations
            self.process_episode()
            self.get_older_posts()
            print(f'Episodes downloaded: {self.episodes_downloaded}')
        finally:
            # Ensure timer restarts even if there's an error
            print("waiting 12 hours")
            threading.Timer(43200, self.timer).start()  # 43200 sec = 12 hours
    # navigate to older posts button 5 times and get last 5 episodes with no repeats/ span id is blog-pager-older-link
    def get_older_posts(self, limit=5):
        try:
            response = requests.get(self.url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            older_posts = soup.find('span', id='blog-pager-older-link')
            processed_urls = set()
            posts_processed = 0
            
            while older_posts and posts_processed < limit:
                older_link = older_posts.find('a')['href']
                
                if older_link in processed_urls:
                    break
                processed_urls.add(older_link)
                
                # Get the older posts page
                self.url = older_link  # Update URL to use existing functions
                print(f'Processing page: {older_link}')
                
                # Use existing process_episode method
                self.process_episode()
                posts_processed += 1
                
                # Get next page of older posts
                response = requests.get(older_link, headers=self.headers)
                soup = BeautifulSoup(response.text, 'html.parser')
                older_posts = soup.find('span', id='blog-pager-older-link')
                
        except requests.RequestException as e:
            print(f'Error fetching older posts: {e}')
        except Exception as e:
            print(f'Error: {e}')




if __name__ == '__main__':
    c2c = C2CScrape()
    # Start initial timer immediately
    c2c.timer()
    # Keep main thread alive with minimal resource usage
    try:
        while True:
            print("waiting for timer")
            print("time is: ", datetime.datetime.now())
            time.sleep(3600)  # Check once per hour
    except KeyboardInterrupt:
        print("\nStopping scheduled downloads...")
    print(f'Episodes downloaded: {c2c.episodes_downloaded}')
    
    #rss = createRss()
    #rss.process_episodes()
