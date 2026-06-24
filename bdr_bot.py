import requests
import pandas as pd
import os
from datetime import datetime

print(f"[{datetime.now()}] Starting automated BDR scan...\n")

# Get API credentials from environment
api_key = os.getenv("PODCASTINDEX_API_KEY")
api_secret = os.getenv("PODCASTINDEX_API_SECRET")

if not api_key or not api_secret:
    print("ERROR: Missing PODCASTINDEX_API_KEY or PODCASTINDEX_API_SECRET")
    exit(1)

# Fetch recent feeds from Podcast Index
print("Fetching latest podcasts from Podcast Index...")
url = "https://api.podcastindex.org/api/1.0/feeds/recent"

headers = {
    "User-Agent": "mowPod-BDR-Bot",
    "X-Podcastindex-Auth": f"{api_key}:{api_secret}"
}

try:
    response = requests.get(url, headers=headers, params={"max": 2000}, timeout=15)
    
    if response.status_code != 200:
        print(f"API Error: {response.status_code}")
        print(f"Response: {response.text[:300]}")
        exit(1)
    
    data = response.json()
    feeds = data.get("feeds", [])
    print(f"✓ Got {len(feeds)} recent podcasts from API\n")
    
    # Convert to DataFrame
    df = pd.DataFrame(feeds)
    
except Exception as e:
    print(f"ERROR fetching from API: {e}")
    exit(1)

print(f"Processing {len(df)} podcasts...\n")

# Approved hosting platforms
approved_hosts = [
    "Acast", "Anchor", "Spotify for Podcasters", "Buzzsprout", "Captivate", 
    "iHeartMedia", "Libsyn", "Megaphone", "Podbean", "Podscribe", 
    "Podsights", "Podtrac", "PRX", "Luminary", "Simplecast", "Spreaker", "Transistor"
]

# Filter 1: Approved hosts only
df = df[df['generator'].fillna('').str.contains('|'.join(approved_hosts), case=False, na=False)]
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
df = df[['title', 'author', 'feedUrl', 'description', 'generator', 'language', 'image']]

# Save qualified leads
output_file = f"podcast_leads_{datetime.now().strftime('%Y%m%d')}.csv"
df.to_csv(output_file, index=False)

print(f"\n✓ Saved {len(df)} qualified leads to {output_file}")
print(f"✓ Ready for manual research")
