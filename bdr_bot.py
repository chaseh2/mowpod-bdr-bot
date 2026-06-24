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

df['host_platform'] = df['url'].apply(get_host_from_url)

# Filter 1: Approved hosting platforms
df = df[df['host_platform'].notna()]
print(f"✓ Approved hosts: {len(df)}")

# Filter 2: English only
df = df[df['language'].fillna('').str.lower().str.startswith('en', na=False)]
print(f"✓ English language: {len(df)}")

# Filter 3: Remove blank image or description
df = df[df['image'].fillna('') != '']
df = df[df['description'].fillna('') != '']
print(f"✓ Complete entries: {len(df)}")

# Convert timeAdded to readable datetime
df['dateAdded'] = pd.to_datetime(df['timeAdded'], unit='s')

# Reorder columns - filter fields first, then all others
filter_cols = ['host_platform', 'language', 'dateAdded']
other_cols = [col for col in df.columns if col not in filter_cols and col != 'dateAdded']
df = df[filter_cols + other_cols]

output_file = f"podcast_leads_{datetime.now().strftime('%Y%m%d')}.csv"
df.to_csv(output_file, index=False)

print(f"\n✓ Saved {len(df)} qualified leads to {output_file}")
print(f"Total columns: {len(df.columns)}")
print(f"Date range: {df['dateAdded'].min()} to {df['dateAdded'].max()}")
