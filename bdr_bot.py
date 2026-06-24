import requests
import pandas as pd
from datetime import datetime
import io

print(f"[{datetime.now()}] Starting automated BDR scan...\n")

# Download the public CSV
csv_url = "https://public.podcastindex.org/newlyAddedFeeds24hours.csv"

print("Downloading latest podcasts from Podcast Index...")
try:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    response = requests.get(csv_url, headers=headers, timeout=30)
    response.raise_for_status()
    
    # Read CSV from response
    df = pd.read_csv(io.StringIO(response.text))
    print(f"✓ Got {len(df)} podcasts\n")
    
except Exception as e:
    print(f"ERROR downloading CSV: {e}")
    exit(1)

print(f"Processing {len(df)} podcasts...\n")

# Approved hosting platforms
approved_hosts = ["Acast", "Anchor", "Spotify for Podcasters", "Buzzsprout", "Captivate", "iHeartMedia", "Libsyn", "Megaphone", "Podbean", "Podscribe", "Podsights", "Podtrac", "PRX", "Luminary", "Simplecast", "Spreaker", "Transistor"]

# Filter 1: Approved hosts only
df = df[df['host'].fillna('').str.contains('|'.join(approved_hosts), case=False, na=False)]
print(f"✓ Approved hosts: {len(df)}")

# Filter 2: English only
df = df[df['language'].fillna('').str.lower().str.startswith('en', na=False)]
print(f"✓ English language: {len(df)}")

# Filter 3: Remove multi-feed authors (spam/AI)
author_counts = df['author'].value_counts()
multi_feed_authors = author_counts[author_counts > 1].index.tolist()
removed_spam = len(multi_feed_authors)
df = df[~df['author'].isin(multi_feed_authors)]
print(f"✓ Removed {removed_spam} spam creators: {len(df)} remaining")

# Filter 4: Remove blank image or description
df = df[df['image'].notna() & (df['image'] != '')]
df = df[df['description'].notna() & (df['description'] != '')]
print(f"✓ Complete entries: {len(df)}")

# Keep useful columns
df = df[['title', 'author', 'url', 'description', 'host', 'language', 'image']]

# Save qualified leads
output_file = f"podcast_leads_{datetime.now().strftime('%Y%m%d')}.csv"
df.to_csv(output_file, index=False)

print(f"\n✓ Saved {len(df)} qualified leads to {output_file}")
print(f"✓ Ready for manual research")
