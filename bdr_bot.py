import anthropic
import json
import requests
import os
from datetime import datetime

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
PODCASTINDEX_KEY = os.getenv("PODCASTINDEX_API_KEY")

print(f"[{datetime.now()}] Starting BDR scan...")

def get_recent_feeds():
    url = "https://api.podcastindex.org/api/1.0/feeds/recent"
    headers = {"User-Agent": "mowPod", "X-Podcastindex-Auth": PODCASTINDEX_KEY}
    try:
        response = requests.get(url, headers=headers, params={"max": 100}, timeout=10)
        if response.status_code == 200:
            return response.json().get("feeds", [])
        print(f"API error: {response.status_code}")
        return []
    except Exception as e:
        print(f"Error: {e}")
        return []

def classify_show(feed):
    try:
        msg = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=100,
            messages=[{"role": "user", "content": f"Brand podcast? Title: {feed.get('title')} Author: {feed.get('author')} JSON: {{\"brand\": bool, \"conf\": 0-1}}"}]
        )
        return json.loads(msg.content[0].text)
    except:
        return {"brand": False, "conf": 0}

def main():
    feeds = get_recent_feeds()
    if not feeds:
        print("No feeds")
        return
    leads = []
    for feed in feeds[:50]:
        result = classify_show(feed)
        if result.get("brand") and result.get("conf", 0) > 0.7:
            leads.append({"title": feed.get("title"), "link": feed.get("link"), "confidence": result.get("conf")})
            print(f"✓ {feed.get('title')}")
    with open(f"bdr_leads_{datetime.now().strftime('%Y%m%d')}.json", "w") as f:
        json.dump(leads, f)
    print(f"Found {len(leads)} leads")

if __name__ == "__main__":
    main()
