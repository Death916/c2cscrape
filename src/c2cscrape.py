#!/usr/bin/env python3

import logging
import os
import re

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
        self.download_amount: int = 5
        self.last_download = None
        self.last_download_link = None
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.episodes_downloaded = 0
        self.download_location = "/downloads"

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
        """
        Get torrent link from page
        Returns a list of torrent links
        """
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
            print(f"Found {len(episode_elems)} episodes")
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

    def generate_nfo_content(self, content):
        lines = [line.strip() for line in content.splitlines()]
        # Remove separator lines if present
        lines = [line for line in lines if not set(line).issubset({"-"}) and line]

        info = {
            "title": "Unknown Title",
            "host": "Unknown Host",
            "guests": [],
            "date": "Unknown Date",
            "description": "",
        }

        # Heuristic parsing
        if lines:
            info["title"] = lines[0]

        desc_lines = []
        parsing_desc = False

        for i, line in enumerate(lines):
            if i == 0:
                continue

            lower_line = line.lower()
            if lower_line.startswith("hosted by"):
                info["host"] = line.split("by", 1)[1].strip()
            elif lower_line.startswith("host:"):
                info["host"] = line.split(":", 1)[1].strip()
            elif lower_line.startswith("guests:") or lower_line.startswith("guest:"):
                if ":" in line:
                    val = line.split(":", 1)[1].strip()
                    if val:
                        info["guests"].append(val)
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    # Check if next line is a date or month, if not, assume it's a guest continuation
                    is_date = any(
                        x in next_line.lower()
                        for x in [
                            "friday",
                            "monday",
                            "tuesday",
                            "wednesday",
                            "thursday",
                            "saturday",
                            "sunday",
                            "january",
                            "february",
                            "march",
                            "april",
                            "may",
                            "june",
                            "july",
                            "august",
                            "september",
                            "october",
                            "november",
                            "december",
                        ]
                    )
                    if not is_date:
                        info["guests"].append(next_line)

            elif any(
                day in lower_line
                for day in [
                    "monday",
                    "tuesday",
                    "wednesday",
                    "thursday",
                    "friday",
                    "saturday",
                    "sunday",
                ]
            ) and any(
                month in lower_line
                for month in [
                    "january",
                    "february",
                    "march",
                    "april",
                    "may",
                    "june",
                    "july",
                    "august",
                    "september",
                    "october",
                    "november",
                    "december",
                ]
            ):
                info["date"] = line
                parsing_desc = True
            elif parsing_desc:
                desc_lines.append(line)
            # Fallback for simple format: if we are deep in file and haven't found date, treat as description
            elif not parsing_desc and i > 3 and not info.get("date") == "Unknown Date":
                desc_lines.append(line)

        info["description"] = "\n".join(desc_lines)

        # Copyright year extraction
        year = "202X"
        if "," in info["date"]:
            try:
                year = info["date"].split(",")[-1].strip()
            except:
                pass

        nfo_template = f"""General Information
===================
 Title:                  {info["title"]}
 Author:                 Coast to Coast AM
 Read By:                {info["host"]}
 Copyright:              (c){year} Premiere Networks
 Genre:                  Talk Radio / Paranormal
 Publisher:              Coast to Coast AM
 Duration:               04:00:00 (Approx)

Media Information
=================
 Source Format:          MP3
 Source Sample Rate:     44100 Hz
 Source Channels:        2
 Source Bitrate:         64 kbits

 Encoded Codec:          MP3
 Encoded Sample Rate:    44100 Hz
 Encoded Channels:       2
 Encoded Bitrate:        64 kbits

Book Description
================
{info["description"]}

Guest(s): {", ".join(info["guests"])}
"""
        return nfo_template

    def add_nfo(self):
        """Add nfo file to episode folders by reading the downloaded .txt"""
        # Ensure we are using the path from the environment
        download_location = os.getenv("QB_DOWNLOAD_PATH") or self.download_location

        if not download_location:
            logging.warning("QB_DOWNLOAD_PATH is not set. Skipping NFO generation.")
            return

        if not os.path.exists(download_location):
            logging.warning(
                f"Download path {download_location} does not exist. Skipping NFO generation."
            )
            return

        logging.info(
            f"Scanning {download_location} for .txt files to generate desc.txt..."
        )

        for root, dirs, files in os.walk(download_location):
            for file in files:
                if file.endswith(".txt") and not file.endswith("_debug.txt"):
                    txt_path = os.path.join(root, file)
                    desc_path = os.path.join(root, "desc.txt")

                    if os.path.exists(desc_path):
                        continue

                    try:
                        with open(txt_path, "r", encoding="utf-8") as f:
                            content = f.read()

                        nfo_content = self.generate_nfo_content(content)

                        # Try to extract date from an mp3 filename in the same folder that begins with "Coast-"
                        date_str = None
                        try:
                            for fname in files:
                                # Look for mp3 files named like "Coast-YYYY-MM-DD.mp3"
                                if fname.lower().startswith(
                                    "coast-"
                                ) and fname.lower().endswith(".mp3"):
                                    # split once on the first hyphen to preserve any extra hyphens in other parts
                                    try:
                                        date_str = fname.split("-", 1)[1].rsplit(
                                            ".", 1
                                        )[0]
                                        # basic sanity check: date contains digits and hyphens
                                        if not any(ch.isdigit() for ch in date_str):
                                            date_str = None
                                        else:
                                            break
                                    except Exception:
                                        date_str = None
                                        continue
                        except Exception:
                            date_str = None

                        # Removed fallback: do not extract date from the .txt filename.
                        # Only mp3 filenames (e.g. Coast-YYYY-MM-DD.mp3) will be used to derive the date.

                        # If we found a date, append it to the Title line in the generated content.
                        if nfo_content and date_str:
                            try:
                                # Replace the Title line while keeping spacing/prefix intact
                                # Matches a line like " Title:                  Some title"
                                nfo_content = re.sub(
                                    r"(^\s*Title:\s*)(.+)$",
                                    lambda m: f"{m.group(1)}{m.group(2)} - {date_str}",
                                    nfo_content,
                                    flags=re.M,
                                )
                            except Exception:
                                # If replacement fails, leave content unchanged and continue
                                logging.debug(
                                    f"Failed to append date to Title for {txt_path}"
                                )

                        if nfo_content:
                            with open(desc_path, "w", encoding="utf-8") as f:
                                f.write(nfo_content)
                            logging.info(f"Created desc.txt: {desc_path}")
                    except Exception as e:
                        logging.error(f"Failed to create desc.txt for {txt_path}: {e}")


class Qbittorrent:
    def __init__(self):
        self.username = ""
        self.password = ""
        self.host = "localhost"
        self.port = 8080
        self.download_path: str = ""

    def get_credentials(self):
        """Get qbittorrent credentials from .env file"""
        load_dotenv()  # gets credentials from env file
        self.username = os.getenv("QB_USERNAME")
        self.password = os.getenv("QB_PASSWORD")
        self.host = os.getenv("QB_HOST")
        self.port = os.getenv("QB_PORT")
        self.download_path = os.getenv("QB_DOWNLOAD_PATH")
        if not self.username or not self.password:
            raise ValueError("QB_USERNAME and QB_PASSWORD must be set in .env file")

    def add_torrent(self, links):
        """
        Add torrents to qbittorrent
        Takes a list of links and adds them to qbittorrent
        """
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
            torrent.auth_log_out()
            logging.info("Logged out of qbittorrent")

        except qbapi.LoginFailed:
            logging.error("Failed to login to qbittorrent")
            raise

        for link in links:
            try:
                # "/" added for creating subdir so abs finds properly
                self.download_path = self.download_path + "/"
                torrent.torrents_add(
                    urls=link, save_path=self.download_path, seeding_time_limit=2
                )

                logging.info(f"Added torrent {link}  to qbittorrent")
            except Exception as e:
                logging.error(f"Error adding torrent {link} to qbittorrent: {e}")
                raise


def main():
    pass


if __name__ == "__main__":
    scraper = TorrentScrape()
    # c2c.get_torrent_link()
    link = scraper.get_torrent_link()
    torrent = Qbittorrent()
    torrent.get_credentials()
    if link:
        torrent.add_torrent(link)

    # Process NFOs for existing downloads
    scraper.add_nfo()
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
