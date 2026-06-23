import anthropic
import csv
import json
import os
from datetime import datetime

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

print(f"[{datetime.now()}] Starting BDR scan...\n")

def classify_show(title, author, description):
    try:
        msg = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=50,
            messages=[{"role": "user", "content": f"Brand/corporate podcast? Title: {title} Author: {author} Desc: {description[:100]} JSON: {{\"brand\": bool, \"conf\": 0-1}}"}]
        )
        return json.loads(msg.content[0].text)
    except:
        return {"brand": False, "conf": 0}

leads = []

with open("newly_added_feeds.csv", "r") as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader):
        if i >= 100:  # Process first 100
            break
        
        title = row.get("title", "")
        author = row.get("author", "")
        description = row.get("description", "")
        
        result = classify_show(title, author, description)
        
        if result.get("brand") and result.get("conf", 0) > 0.7:
            leads.append({
                "title": title,
                "author": author,
                "confidence": result.get("conf")
            })
            print(f"✓ {title}")

with open(f"bdr_leads_{datetime.now().strftime('%Y%m%d')}.json", "w") as f:
    json.dump(leads, f, indent=2)

print(f"\n✓ Found {len(leads)} branded podcasts")
