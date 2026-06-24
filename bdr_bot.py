import pandas as pd
from datetime import datetime

# Read the daily CSV you upload
df = pd.read_csv("newly_added_feeds.csv")

print(f"[{datetime.now()}] Processing {len(df)} podcasts...\n")

# Approved hosting platforms
approved_hosts = [
    "Acast", "Anchor", "Spotify for Podcasters", "Buzzsprout", "Captivate", 
    "iHeartMedia", "Libsyn", "Megaphone", "Podbean", "Podscribe", 
    "Podsights", "Podtrac", "PRX", "Luminary", "Simplecast", "Spreaker", "Transistor"
]

# Filter 1: Approved hosts only
df = df[df['host'].fillna('').str.contains('|'.join(approved_hosts), case=False, na=False)]
print(f"✓ Approved hosts: {len(df)}")

# Filter 2: English only
df = df[df['language'].fillna('').str.startswith('en', na=False)]
print(f"✓ English language: {len(df)}")

# Filter 3: Remove multi-feed authors (spam/AI)
author_counts = df['author'].value_counts()
multi_feed_authors = author_counts[author_counts > 1].index.tolist()
df = df[~df['author'].isin(multi_feed_authors)]
print(f"✓ Removed {len(multi_feed_authors)} spam creators: {len(df)} remaining")

# Filter 4: Remove blank image or description
df = df[df['image'].notna() & (df['image'] != '')]
df = df[df['description'].notna() & (df['description'] != '')]
print(f"✓ Complete entries: {len(df)}")

# Save qualified leads
output_file = f"podcast_leads_{datetime.now().strftime('%Y%m%d')}.csv"
df.to_csv(output_file, index=False)

print(f"\n✓ Saved {len(df)} qualified leads to {output_file}")
