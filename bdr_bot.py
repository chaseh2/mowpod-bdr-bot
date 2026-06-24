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
    
    # DEBUG: Print all columns and check if author exists
    print(f"Available columns: {list(df.columns)}")
    print(f"Has 'author' column: {'author' in df.columns}")
    if 'author' in df.columns:
        print(f"Non-null authors: {df['author'].notna().sum()}")
        print(f"Sample authors: {df['author'].dropna().head().tolist()}")
    print()
    
except Exception as e:
    print(f"ERROR: {e}")
    exit(1)
