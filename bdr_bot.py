import anthropic
import json
import requests
import os
import sys
from datetime import datetime, timedelta

sys.stdout.flush()

print(f"[{datetime.now()}] Starting BDR scan...", flush=True)

# Check for required API keys
if not os.getenv("ANTHROPIC_API_KEY"):
    print("ERROR: ANTHROPIC_API_KEY not set")
    exit(1)

if not os.getenv("PODCASTINDEX_API_KEY"):
    print("ERROR: PODCASTINDEX_API_KEY not set")
    exit(1)

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ============================================
# STEP 1: Get Recent Feeds from Podcast Index
# ============================================

def get_recent_podcast_feeds(hours=24, limit=100):
    """Query Podcast Index for recently updated feeds"""
    try:
        url = "https://api.podcastindex.org/api/1.0/feeds/recent"
        api_key = os.getenv("PODCASTINDEX_API_KEY")
        api_secret = os.getenv("PODCASTINDEX_API_SECRET")
        
        headers = {
            "User-Agent": "mowPod-BDR-Bot",
            "X-Podcastindex-Auth": f"{api_key}:{api_secret}"
        }
        
        params = {"max": limit}
        
        print(f"Fetching from Podcast Index... (last {hours} hours)", flush=True)
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        print(f"Response status: {response.status_code}", flush=True)
        
        if response.status_code != 200:
            print(f"API Error: {response.text[:500]}", flush=True)
            return []
        
        data = response.json()
        feeds = data.get("feeds", [])
        print(f"✓ Got {len(feeds)} feeds", flush=True)
        return feeds
        
    except Exception as e:
        print(f"ERROR fetching feeds: {e}", flush=True)
        return []


# ============================================
# STEP 2: Classify - Is it a Brand Show?
# ============================================

def classify_brand_show(feed):
    """Use Claude to determine if this is a corporate/brand show"""
    try:
        prompt = f"""Analyze this podcast and determine if it's a brand/corporate show (produced or sponsored by a company for marketing).

Title: {feed.get('title', 'N/A')}
Author: {feed.get('author', 'N/A')}
Description: {feed.get('description', 'N/A')[:500]}

Is this a brand/corporate show? Respond in JSON:
{{
  "is_brand_show": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "brief"
}}"""
        
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text
        result = json.loads(response_text)
        return result
        
    except Exception as e:
        print(f"  Classification error: {e}", flush=True)
        return {"is_brand_show": False, "confidence": 0, "reasoning": "Error"}


# ============================================
# MAIN RUN
# ============================================

def run_daily_bdr_scan():
    """Execute the scan"""
    print(f"[{datetime.now()}] Starting BDR scan...", flush=True)
    
    # Get feeds
    feeds = get_recent_podcast_feeds(hours=24, limit=50)
    
    if not feeds:
        print("No feeds fetched. Check API key and Podcast Index status.", flush=True)
        return
    
    qualified_leads = []
    
    for i, feed in enumerate(feeds[:20]):  # Test on first 20
        title = feed.get('title', 'Unknown')
        print(f"\n[{i+1}] {title}", flush=True)
        
        # Classify
        classification = classify_brand_show(feed)
        
        if classification.get("is_brand_show") and classification.get("confidence", 0) > 0.6:
            print(f"  ✓ Qualified ({classification.get('confidence', 0):.0%})", flush=True)
            qualified_leads.append({
                "show_title": title,
                "website": feed.get('link'),
                "classification_confidence": classification.get("confidence"),
                "reasoning": classification.get("reasoning")
            })
    
    # Save results
    output_file = f"bdr_leads_{datetime.now().strftime('%Y%m%d')}.json"
    with open(output_file, "w") as f:
        json.dump(qualified_leads, f, indent=2)
    
    print(f"\n✓ Complete. Found {len(qualified_leads)} qualified leads", flush=True)
    print(f"✓ Saved to {output_file}", flush=True)


if __name__ == "__main__":
    run_daily_bdr_scan()
