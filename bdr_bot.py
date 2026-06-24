import requests
import pandas as pd
from datetime import datetime
import hashlib
import time
import os

print(f"[{datetime.now()}] Starting automated BDR scan...\n")

# Get API credentials from environment
api_key = os.getenv("PODCASTINDEX_API_KEY")
api_secret = os.getenv("PODCASTINDEX_API_SECRET")

if not api_key or not api_secret:
    print("ERROR: Missing API credentials")
    exit(1)

# Correct endpoint: /recent/newfeeds
api_url = "https://api.podcastindex.org/api/1.0/recent/newfeeds"

# Get current timestamp
auth_date = str(int(time.time()))

# Create SHA1 hash: apiKey + apiSecret + timestamp
auth_hash = hashlib.sha1(f"{api_key}{api_secret}{auth_date}".encode()).hexdigest()

# Set required headers
headers = {
    "User-Agent": "mowPod-BDR-Bot/1.0",
    "X-Auth-Date": auth_date,
    "X-Auth-Key": api_key,
    "Authorization": auth_hash
}

print("Fetching latest podcasts from Podcast Index...")
try:
    response = requests.get(api_url, headers=headers, params={"max": 2000}, timeout=30)
    
    if response.status_code != 200:
        print(f"API Error: {response.status_code}")
        print(f"Response: {response.text[:300]}")
        exit(1)
    
    data = response.json()
    feeds = data.get("feeds", [])
    print(f"✓ Got {len(feeds)} podcasts from API\n")
    
    # Convert to DataFrame
    df = pd.DataFrame(feeds)
    
except Exception as e:
    print(f"ERROR fetching from API: {e}")
    exit(1)

print(f"Processing {len(df)} podcasts...\n")

# Approved hosting platforms
approved_hosts = ["Acast", "Anchor", "Spotify for Podcasters", "Buzzsprout", "Captivate", "iHeartMedia", "Libsyn", "Megaphone", "Podbean", "Podscribe", "Podsights", "Podtrac", "PRX", "Luminary", "Simplecast", "Spreaker", "Transistor"]

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
