import requests
import pandas as pd
from datetime import datetime
import hashlib
import time
import io

print(f"[{datetime.now()}] Starting automated BDR scan...\n")

# Get API credentials from environment
api_key = os.getenv("PODCASTINDEX_API_KEY")
api_secret = os.getenv("PODCASTINDEX_API_SECRET")

if not api_key or not api_secret:
    print("ERROR: Missing API credentials")
    exit(1)

# Podcast Index API requires Amazon-style request signing
api_url = "https://api.podcastindex.org/api/1.0/feeds/recent"

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
df = df[df['language'].f
