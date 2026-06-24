import requests
import pandas as pd
from datetime import datetime
import io

print(f"[{datetime.now()}] Starting automated BDR scan...\n")

# Download the public CSV
csv_url = "https://public.podcastindex.org/newlyAddedFeeds24hours.csv"

print("Downloading latest podcasts from Podcast Index...")
try:
    response = requests.get(csv_url, timeout=30)
    response.raise_for_status()
    
    # Read CSV from response
    df = pd.read_csv(io.StringIO(response.text))
    print(f"✓ Got {len(df)} podcasts\n")
    
except Exception as e:
    print(f"ERROR downloading CSV: {e}")
    exit(1)

print(f"Processing {len(df)} podcasts...\n")

# Approved hosting platforms
approved_hosts = [
    "Acast", "Anchor", "Spotify for Podcasters", "Buzzsprout", "Captivate", 
    "iHeartMedia", "Libsyn", "Megaphone", "Podbean", "Podscribe", 
    "Podsights", "Podtrac", "PRX",
