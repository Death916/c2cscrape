#!/usr/bin/env python3

import datetime
import logging
import os
import random
import re
import time

import qbittorrentapi as qbapi
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


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
            logging.info(f"Page fetched successfully")
            logging.debug(f"Response status code: {response.status_code}")
            return response.text
        except requests.RequestException as e:
            logging.error(f"Error fetching page: {e}")
            return None

    def get_torrent_link(self):
        links = []
        page = self.get_torrent_page()
        if not page:
            logging.error("No page found")
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
                logging.info(
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
                    logging.warning(
                        f"Skipping episode {title}, as it doesn't start with 'Coast'"
                    )
                    continue
                link = a.get("href")
                links.append(link)
                self.episodes_downloaded += 1
                logging.info(f"found episode {title}")
                logging.debug(f"link: {link}")

            logging.info("done")
            logging.info(f"Downloaded {self.episodes_downloaded} episodes")
            logging.info("Returning link to qbit")
            return links  # need to return link later to qbit but need to decide logic


class Qbittorrent:
    def __init__(self):
        self.username = ""
        self.password = ""
        self.host = "localhost"
        self.port = 8080

    def get_credentials(self):
        # Get qbittorrent credentials from .env file
        load_dotenv()  # gets credentials from env file
        self.username = os.getenv("QB_USERNAME")
        self.password = os.getenv("QB_PASSWORD")
        self.host = os.getenv("QB_HOST")
        self.port = os.getenv("QB_PORT")
        self.download_path = os.getenv("QB_DOWNLOAD_PATH")
        if not self.username or not self.password:
            raise ValueError("QB_USERNAME and QB_PASSWORD must be set in .env file")

    def add_torrent(self, links):
        conn_info = dict(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
        )
        logging.info(f"Logging in as {self.username} to host {self.host}:{self.port}")
        torrent = qbapi.Client(**conn_info)
        try:
            torrent.auth_log_in()
            logging.info("Logged in to qbittorrent")
            logging.info(f"qbittorrent version: {torrent.app.version}")

        except qbapi.LoginFailed:
            logging.error("Failed to login to qbittorrent")
            raise

        for link in links:
            try:
                torrent.torrents_add(urls=link, save_path=self.download_path)
                logging.info(f"Added torrent {link} to qbittorrent")
            except Exception as e:
                logging.error(f"Error adding torrent {link} to qbittorrent: {e}")
                raise


def main():
    pass


if __name__ == "__main__":
    c2c = TorrentScrape()
    # c2c.get_torrent_link()
    link = c2c.get_torrent_link()
    torrent = Qbittorrent()
    torrent.get_credentials()
    torrent.add_torrent(link)
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
