import requests
import pandas as pd
from datetime import datetime
import hashlib
import time
import os
from urllib.parse import urlparse

print(f"[{datetime.now()}] Starting automated BDR scan...\n")

api_key = os.getenv("PODCASTINDEX_API_KEY")
api_secret = os.getenv("PODCASTINDEX_API_SECRET")

if not api_key or not api_secret:
    print("ERROR: Missing API credentials")
    exit(1)

api_url = "https://api.podcastindex.org/api/1.0/recent/newfeeds"
auth_date = str(int(time.time()))
auth_hash = hashlib.sha1(f"{api_key}{api_secret}{auth_date}".encode()).hexdigest()

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
        exit(1)
    
    data = response.json()
    feeds = data.get("feeds", [])
    print(f"✓ Got {len(feeds)} podcasts from API\n")
    
    df = pd.DataFrame(feeds)
    
except Exception as e:
    print(f"ERROR: {e}")
    exit(1)

print(f"Processing {len(df)} podcasts...\n")

# Map domain names to approved hosting platforms
host_mapping = {
    'anchor.fm': 'Anchor',
    'podbean.com': 'Podbean',
    'buzzsprout.com': 'Buzzsprout',
    'transistor.fm': 'Transistor',
    'spreaker.com': 'Spreaker',
    'libsyn.com': 'Libsyn',
    'megaphone.fm': 'Megaphone',
    'omnycontent.com': 'Megaphone',
    'acast.com': 'Acast',
    'captivate.fm': 'Captivate',
    'podtrac.com': 'Podtrac',
    'redcircle.com': 'Spotify for Podcasters',
    'podsights.podtrac.com': 'Podsights',
    'simplecast.com': 'Simplecast',
    'prx.org': 'PRX',
    'luminary.link': 'Luminary',
    'podscribe.com': 'Podscribe',
    'iheartmedia.com': 'iHeartMedia',
}

def get_host_from_url(url):
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        if domain in host_mapping:
            return host_mapping[domain]
        for known_domain, host in host_mapping.items():
            if known_domain in domain:
                return host
        return None
    except:
        return None

def get_first_three_words(title):
    if pd.isna(title):
        return None
    words = str(title).split()[:3]
    return ' '.join(words) if words else None

df['host_platform'] = df['url'].apply(get_host_from_url)

# Filter 1: Approved hosting platforms
df = df[df['host_platform'].notna()]
print(f"✓ Approved hosts: {len(df)}")

# Filter 2: English language only
df = df[df['language'].fillna('').str.lower().str.startswith('en', na=False)]
print(f"✓ English language: {len(df)}")

# Filter 3: Remove blank image or description
df = df[df['image'].fillna('') != '']
df = df[df['description'].fillna('') != '']
print(f"✓ Complete entries: {len(df)}")

# Filter 4: Remove duplicate descriptions
description_counts = df['description'].value_counts()
duplicate_descriptions = description_counts[description_counts > 1].index.tolist()
removed_dupes = len(duplicate_descriptions)
df = df[~df['description'].isin(duplicate_descriptions)]
print(f"✓ Removed {removed_dupes} duplicate descriptions: {len(df)} remaining")

# Filter 5: Keep 1 per group of same first 3 words in title
df['title_prefix'] = df['title'].apply(get_first_three_words)
df = df.drop_duplicates(subset=['title_prefix'], keep='first')
df = df.drop('title_prefix', axis=1)
print(f"✓ Removed title duplicates (same first 3 words): {len(df)} remaining")

print(f"\nFetching author data for {len(df)} qualified leads...\n")

# Batch-fetch author data via /podcasts/byfeedid
def get_author_from_api(feed_id):
    try:
        auth_date = str(int(time.time()))
        auth_hash = hashlib.sha1(f"{api_key}{api_secret}{auth_date}".encode()).hexdigest()
        
        headers = {
            "User-Agent": "mowPod-BDR-Bot/1.0",
            "X-Auth-Date": auth_date,
            "X-Auth-Key": api_key,
            "Authorization": auth_hash
        }
        
        url = f"https://api.podcastindex.org/api/1.0/podcasts/byfeedid?id={feed_id}"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('feed'):
                return data['feed'].get('author')
        return None
    except:
        return None

# Batch fetch authors with delay to avoid rate limiting
authors = []
for idx, feed_id in enumerate(df['id']):
    author = get_author_from_api(feed_id)
    authors.append(author)
    
    if (idx + 1) % 10 == 0:
        print(f"  Fetched {idx + 1}/{len(df)} authors...")
        time.sleep(1)

df['author'] = authors

# Filter 6: Remove multi-feed authors (spam/AI)
author_counts = df['author'].value_counts()
multi_feed_authors = author_counts[author_counts > 1].index.tolist()
removed_spam = len(multi_feed_authors)
df = df[~df['author'].isin(multi_feed_authors)]
print(f"✓ Removed {removed_spam} spam creators: {len(df)} remaining\n")

# Convert timeAdded to readable datetime
if 'timeAdded' in df.columns:
    df['dateAdded'] = pd.to_datetime(df['timeAdded'], unit='s')

# Reorder columns with priority fields first
priority_cols = ['title', 'author', 'url', 'description', 'host_platform', 'language', 'image', 'dateAdded']
other_cols = [col for col in df.columns if col not in priority_cols]
final_cols = [col for col in priority_cols if col in df.columns] + other_cols
df = df[final_cols]

output_file = f"podcast_leads_{datetime.now().strftime('%Y%m%d')}.csv"
df.to_csv(output_file, index=False)

print(f"✓ Saved {len(df)} qualified leads to {output_file}")
print(f"Total columns: {len(df.columns)}")
