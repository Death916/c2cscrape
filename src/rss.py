from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import os
from c2cscrape import C2CScrape

def create_podcast_feed(directory, title, description, base_url):
    fg = FeedGenerator()
    fg.load_extension('podcast')
    fg.title(title)
    fg.description(description)
    fg.link(href=base_url, rel='alternate')
    fg.language('en')
    fg.podcast.itunes_category('News', 'News Commentary')
    fg.podcast.itunes_explicit('no')
    
    for filename in sorted(os.listdir(directory), reverse=True):
        if filename.lower().endswith('.mp4'):
            fe = fg.add_entry()
            title = filename.replace('.mp4', '')
            fe.title(title)
            fe.link(href=f"{base_url}/downloads/{filename}")
            
            file_path = os.path.join(directory, filename)
            file_stats = os.stat(file_path)
            
            fe.published(datetime.now(timezone.utc))
            fe.description(title)
            fe.id(f"{base_url}/downloads/{filename}")
            fe.enclosure(f"{base_url}/downloads/{filename}", str(file_stats.st_size), 'video/mp4')
    
    return fg

if __name__ == "__main__":
    # Configure feed settings
    videos_dir = "downloads"
    feed_title = "Coast to Coast AM Episodes"
    feed_description = "Latest Coast to Coast AM Episodes"
    base_url = "http://100.79.3.68:8000"  # Replace with your public IP or domain
    
    # Generate the feed
    feed = create_podcast_feed(videos_dir, feed_title, feed_description, base_url)
    feed.rss_file('podcast_feed.xml')
