#!/usr/bin/env python3

import datetime
import os
import random
import re
import time

import requests
from bs4 import BeautifulSoup


class TorrentScrape:
    def __init__(self):
        self.url = "https://knaben.org/search/coast%20to%20coast%20am/0/1/date"
        self.episodes = []
        self.download_amount = 5
        self.last_download = None
        self.last_download_link = None
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.episodes_downloaded = 0
        self.download_location = "/downloads"

    def sanitize_filename(self, filename):
        # Remove or replace invalid filename characters
        return re.sub(r'[<>:"/\\|?*]', "-", filename)

    def get_torrent_page(self):
        try:
            response = requests.get(self.url, headers=self.headers)
            response.raise_for_status()
            print(response)
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching page: {e}")
            return None

    def get_episode_info(self):
        page = self.get_torrent_page()
        if not page:
            print("No page found")
            return None

        soup = BeautifulSoup(page, "html.parser")
        main_class = soup.find("div", class_="p-3")

        if not main_class:
            print("No main class found")
            return None

        episode_elems = main_class.select(".text-wrap.w-100")
        if episode_elems:
            print(
                f"Found {len(episode_elems)} episode elements using selector .text-wrap.w-100"
            )
            if len(episode_elems) > self.download_amount:
                print(
                    f"Too many episodes found, only downloading last {self.download_amount}"
                )
                episode_elems = episode_elems[: self.download_amount]
            for ep in episode_elems:
                a = ep.find("a")
                if not a:
                    continue
                title = a.get("title") or a.get_text(strip=True)
                # skip episodes that don't start with "Coast" as sometimes they show up in search
                if not title.startswith("Coast"):
                    print(f"Skipping episode {title}")
                    continue
                link = a.get("href")
                self.episodes_downloaded += 1
                print(f"found episode {title}")
                # print(f"link: {link}")

            print("done")
            return  # need to return link later to qbit but need to decide logic


class Qbittorrent:
    pass


if __name__ == "__main__":
    c2c = TorrentScrape()
    c2c.get_episode_info()
    # Keep main thread alive with minimal resource usage
"""
    try:
        while True:
            print("waiting for timer")
            print("time is: ", datetime.datetime.now())
            time.sleep(3600)  # Check once per hour

    except KeyboardInterrupt:
        print("\nStopping scheduled downloads...")
    print(f"Episodes downloaded: {c2c.episodes_downloaded}")
"""
# rss = createRss()
# rss.process_episodes()
