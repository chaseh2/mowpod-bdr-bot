import anthropic
import csv
import json
import os
import requests
from datetime import datetime
from xml.etree import ElementTree as ET

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

print(f"[{datetime.now()}] Starting BDR scan...\n")

def fetch_feed_details(feed_url):
    """Fetch actual RSS feed and extract details"""
    try:
        response = requests.get(feed_url, timeout=5)
        root = ET.fromstring(response.content)
        
        # Extract feed metadata
        channel = root.find('channel')
        if channel is None:
            return None
        
        description = channel.findtext('description', '')[:300]
        link = channel.findtext('link', '')
        category = channel.findtext('category', '')
        owner = channel.find('.//owner')
        owner_name = owner.findtext('name', '') if owner is not None else ''
        
        return {
            "description": description,
            "link": link,
            "category": category,
            "owner": owner_name
        }
    except Exception as e:
        return None

ddef classify_show(title, author, feed_details):
    """Classify based on actual feed content"""
    if not feed_details:
        return {"brand": False, "conf": 0}
    
    try:
        prompt = f"""You are a BDR expert identifying brand/corporate podcasts.

DEFINITION: A brand podcast is produced/sponsored by a company to promote their business, services, or brand.

EXAMPLES OF BRAND PODCASTS:
- "Keller Williams Connect" (real estate company)
- "Shopify Masters" (Shopify's podcast)
- "HubSpot's The Hubspot Podcast Network" (HubSpot)
- "Master Podcast Marketing by Amp 99" (marketing agency)
- "Based Academy" (education/training company)

PODCAST DATA:
Title: {title}
Author: {author}
Description: {feed_details.get('description', '')}
Owner: {feed_details.get('owner', '')}
Website: {feed_details.get('link', '')}

INDICATORS TO CHECK:
1. Company name appears in title or author
2. Words like "Academy", "Realty", "Solutions", "Hub", "Network", "Masters"
3. Description mentions company services
4. Official company branding
5. Author is a company, not a person

IS THIS A BRAND PODCAST? (Yes/No)
Respond ONLY in JSON: {{"brand": true/false, "conf": 0.0-1.0}}"""
        
        msg = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=50,
            messages=[{"role": "user", "content": prompt}]
        )
        result = json.loads(msg.content[0].text)
        return result
    except Exception as e:
        print(f"Error: {e}")
        return {"brand": False, "conf": 0}
leads = []
processed = 0

with open("newly_added_feeds.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if processed >= 50:  # Limit to 50 (API costs)
            break
        
        title = row.get("title", "").strip()
        author = row.get("author", "").strip()
        feed_url = row.get("url", "").strip()
        
        if not title or not feed_url:
            continue
        
        processed += 1
        print(f"[{processed}] Researching: {title}...", end=" ")
        
        # Fetch actual feed
        feed_details = fetch_feed_details(feed_url)
        
        # Classify
        result = classify_show(title, author, feed_details)
        
        if result.get("brand") and result.get("conf", 0) > 0.6:
            leads.append({
                "title": title,
                "author": author,
                "feed_url": feed_url,
                "confidence": round(result.get("conf", 0), 2)
            })
            print("✓ BRAND")
        else:
            print("✗")

with open(f"bdr_leads_{datetime.now().strftime('%Y%m%d')}.json", "w") as f:
    json.dump(leads, f, indent=2)

print(f"\n✓ Processed {processed} feeds")
print(f"✓ Found {len(leads)} branded podcasts")
