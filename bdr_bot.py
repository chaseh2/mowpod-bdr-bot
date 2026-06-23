import anthropic
import csv
import json
import os
from datetime import datetime

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

print(f"[{datetime.now()}] Starting BDR scan...\n")

def classify_show(title, author, generator):
    """Classify if brand podcast based on available data"""
    try:
        # Use title, author, and generator info
        info = f"Title: {title} | Author: {author} | Generator: {generator}"
        
        msg = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=50,
            messages=[{"role": "user", "content": f"Is this a BRAND or CORPORATE podcast (made by a company for marketing)? {info}\n\nRespond JSON: {{\"brand\": bool, \"conf\": 0-1}}"}]
        )
        return json.loads(msg.content[0].text)
    except:
        return {"brand": False, "conf": 0}

leads = []
processed = 0

with open("newlyAddedFeeds24hours.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if processed >= 100:  # Limit to 100 for cost
            break
        
        title = row.get("title", "").strip()
        author = row.get("author", "").strip()
        generator = row.get("generator", "").strip()
        
        # Skip empty entries
        if not title:
            continue
        
        processed += 1
        result = classify_show(title, author, generator)
        
        if result.get("brand") and result.get("conf", 0) > 0.6:  # Lower threshold
            leads.append({
                "title": title,
                "author": author,
                "generator": generator,
                "confidence": round(result.get("conf", 0), 2)
            })
            print(f"✓ {title} ({result.get('conf', 0):.0%})")

with open(f"bdr_leads_{datetime.now().strftime('%Y%m%d')}.json", "w") as f:
    json.dump(leads, f, indent=2)

print(f"\n✓ Processed {processed} feeds")
print(f"✓ Found {len(leads)} branded podcasts")
