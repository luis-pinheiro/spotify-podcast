import os
import re
import datetime
import email.utils
from xml.sax.saxutils import escape
from mutagen.mp3 import MP3

# ==============================================================================
# CONFIGURATION
# Modify these values to customize your podcast feed.
# ==============================================================================
BASE_URL = "https://luis-pinheiro.github.io/spotify-podcast/"  # MUST end with a slash '/'
FEED_TITLE = "Evangelho de Tomé, Eclesiastes, Provérbios e Sabedoria"
FEED_DESCRIPTION = "Áudios gravados dos livros de Eclesiastes, Provérbios, Sabedoria e o Evangelho de Tomé."
FEED_LINK = "https://yourusername.github.io/spotify-podcast/"
FEED_LANGUAGE = "pt-BR"
FEED_AUTHOR = "Luis Pinheiro"
FEED_EMAIL = "luispinheiro35@hotmail.com"
FEED_CATEGORY = "Religion & Spirituality"
FEED_IMAGE = "https://luis-pinheiro.github.io/spotify-podcast/cover.jpg"  # Recommended 1400x1400 to 3000x3000px
FEED_EXPLICIT = "no"  # "yes" or "no"
OUTPUT_FILENAME = "podcast.xml"

# Optional: Starting publication date for the first episode (oldest).
# Each subsequent episode will be published 1 hour later than the previous one,
# ensuring they appear in the correct order in your podcast player.
START_DATE = datetime.datetime(2026, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
# ==============================================================================

def natural_sort_key(s):
    """Sort strings containing numbers in human/natural order."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def format_title(filename):
    """Generates a clean user-friendly title based on the filename patterns."""
    name, _ = os.path.splitext(filename)
    
    # Match "ECLESIASTES CAPITULO X"
    m = re.match(r'^ECLESIASTES\s+CAPITULO\s+(\d+)$', name, re.IGNORECASE)
    if m:
        return f"Eclesiastes - Capítulo {m.group(1)}"
    
    # Match "PROVERBIOS CAPITULO X"
    m = re.match(r'^PROVERBIOS\s+CAPITULO\s+(\d+)$', name, re.IGNORECASE)
    if m:
        return f"Provérbios - Capítulo {m.group(1)}"
    
    # Match "SABEDORIA CAPITULO X"
    m = re.match(r'^SABEDORIA\s+CAPITULO\s+(\d+)$', name, re.IGNORECASE)
    if m:
        return f"Sabedoria - Capítulo {m.group(1)}"
        
    # Match "Evangelho_Tome_dito_X"
    m = re.match(r'^Evangelho_Tome_dito_(\d+)$', name, re.IGNORECASE)
    if m:
        return f"Evangelho de Tomé - Dito {m.group(1)}"
        
    # Fallback to replacing underscores and dashes
    return name.replace('_', ' ').replace('-', ' ').title()

def format_duration(seconds):
    """Format duration in seconds to HH:MM:SS or MM:SS."""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def main():
    print("Scanning directory for MP3 files...")
    all_files = [f for f in os.listdir('.') if f.lower().endswith('.mp3')]
    
    # Sort files naturally so that Capitulo 2 comes before Capitulo 10, etc.
    all_files.sort(key=natural_sort_key)
    
    total_files = len(all_files)
    print(f"Found {total_files} MP3 files.")
    
    if total_files == 0:
        print("No MP3 files found. Please make sure to run this script in the directory containing the audio files.")
        return

    items_xml = []
    current_pub_date = START_DATE

    for idx, filename in enumerate(all_files):
        filepath = os.path.join('.', filename)
        file_size = os.path.getsize(filepath)
        
        # Calculate duration using mutagen
        try:
            audio = MP3(filepath)
            duration_seconds = int(audio.info.length)
            duration_str = format_duration(duration_seconds)
        except Exception as e:
            print(f"Warning: Could not read metadata for {filename}: {e}. Using fallback.")
            duration_str = "00:00"

        # Generate clean title and URL
        title = format_title(filename)
        # URL escape filename (replace spaces with %20, etc.)
        encoded_filename = escape(filename).replace(" ", "%20")
        episode_url = f"{BASE_URL}{encoded_filename}"
        
        # Format RFC 2822 date for RSS
        pub_date_str = email.utils.formatdate(current_pub_date.timestamp(), usegmt=True)
        
        # Unique ID for the episode
        guid = episode_url

        item_xml = f"""    <item>
      <title>{escape(title)}</title>
      <description>Áudio do arquivo {escape(filename)}.</description>
      <pubDate>{pub_date_str}</pubDate>
      <enclosure url="{episode_url}" length="{file_size}" type="audio/mpeg"/>
      <guid isPermaLink="false">{escape(guid)}</guid>
      <itunes:duration>{duration_str}</itunes:duration>
      <itunes:explicit>{FEED_EXPLICIT}</itunes:explicit>
    </item>"""
        items_xml.append(item_xml)
        
        # Increment publication date by 1 hour for each next episode
        # so they remain in sequential order in feed readers
        current_pub_date += datetime.timedelta(hours=1)

    # Generate full RSS feed
    rss_feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" 
     xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" 
     xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>{escape(FEED_TITLE)}</title>
    <description>{escape(FEED_DESCRIPTION)}</description>
    <link>{escape(FEED_LINK)}</link>
    <language>{escape(FEED_LANGUAGE)}</language>
    <itunes:image href="{escape(FEED_IMAGE)}"/>
    <itunes:category text="{escape(FEED_CATEGORY)}"/>
    <itunes:explicit>{FEED_EXPLICIT}</itunes:explicit>
    <itunes:author>{escape(FEED_AUTHOR)}</itunes:author>
    <itunes:owner>
      <itunes:name>{escape(FEED_AUTHOR)}</itunes:name>
      <itunes:email>{escape(FEED_EMAIL)}</itunes:email>
    </itunes:owner>
    <generator>Custom Python RSS Generator</generator>
    
    <!-- Podcast Episodes -->
{chr(10).join(items_xml)}
  </channel>
</rss>
"""

    with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
        f.write(rss_feed)
        
    print(f"\nSuccess! Generated feed saved to: {OUTPUT_FILENAME}")
    print(f"Total episodes generated: {total_files}")
    print("\nNext Steps:")
    print(f"1. Host the generated '{OUTPUT_FILENAME}' and your MP3 files at the BASE_URL ({BASE_URL}).")
    print("2. Submit your RSS feed URL to Spotify for Podcasters (https://podcasters.spotify.com/).")

if __name__ == "__main__":
    main()
