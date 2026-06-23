import anthropic
import json
from datetime import datetime, timedelta
import requests

client = anthropic.Anthropic(api_key="YOUR_API_KEY")

# ============================================
# STEP 1: Get Recent Feeds from Podcast Index
# ============================================

def get_recent_podcast_feeds(hours=24, limit=500):
    """Query Podcast Index for recently updated feeds"""
    url = "https://api.podcastindex.org/api/1.0/feeds/recent"
    
    headers = {
        "User-Agent": "mowPod-BDR-Bot",
        "X-Podcastindex-Auth": "YOUR_API_KEY",  # Get from podcastindex.org
    }
    
    params = {
        "max": limit,
        "since": int((datetime.now() - timedelta(hours=hours)).timestamp())
    }
    
    response = requests.get(url, headers=headers, params=params)
    feeds = response.json()["feeds"]
    return feeds


# ============================================
# STEP 2: Classify - Is it a Brand Show?
# ============================================

def classify_brand_show(feed):
    """Use Claude to determine if this is a corporate/brand show"""
    
    prompt = f"""Analyze this podcast and determine if it's a brand/corporate show (produced or sponsored by a company for marketing).

Title: {feed.get('title', 'N/A')}
Author: {feed.get('author', 'N/A')}
Description: {feed.get('description', 'N/A')[:500]}
Website: {feed.get('link', 'N/A')}

Is this a brand/corporate show? Consider:
- Company-produced content (Slack, Shopify, Microsoft, etc.)
- Sponsored/branded shows (FanDuel, sports betting, fintech brands)
- B2B company podcasts
- Agency/consultancy shows

Exclude:
- Independent creator shows
- Traditional media (NPR, BBC)
- Personal projects

Respond in JSON:
{{
  "is_brand_show": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation",
  "company_name": "extracted company name if applicable"
}}"""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )
    
    # Parse JSON response
    response_text = message.content[0].text
    try:
        result = json.loads(response_text)
    except:
        # Fallback if JSON parsing fails
        result = {"is_brand_show": False, "confidence": 0, "reasoning": "Parse error"}
    
    return result


# ============================================
# STEP 3: Extract Data from Website w/ Vision
# ============================================

def extract_producer_info_from_website(feed_url, show_title):
    """
    Use Claude Vision to screenshot the feed URL and extract:
    - Producer/host names
    - LinkedIn profiles
    - Email
    - Company info
    """
    
    # Get a screenshot of the website using a free service
    screenshot_url = f"https://api.screenshotmachine.com?url={feed_url}&dimension=1024x768"
    
    # Fetch the screenshot
    screenshot_response = requests.get(screenshot_url)
    image_data = screenshot_response.content
    
    # Convert to base64
    import base64
    image_base64 = base64.standard_b64encode(image_data).decode("utf-8")
    
    prompt = f"""Extract producer/host information from this podcast website screenshot.

Show: {show_title}

Find and extract:
1. Host/producer names (primary contact)
2. LinkedIn URLs/profiles
3. Email addresses
4. Company name
5. Location (if mentioned)

Respond in JSON:
{{
  "hosts": [
    {{"name": "John Doe", "linkedin": "linkedin.com/in/johndoe", "email": null}}
  ],
  "company": "Brand Name",
  "location": "USA/Canada/UK",
  "confidence": 0.8,
  "extraction_notes": "where you found this info"
}}"""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": image_base64
                    }
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }]
    )
    
    response_text = message.content[0].text
    try:
        result = json.loads(response_text)
    except:
        result = {"hosts": [], "company": "Unknown", "extraction_notes": "Parse error"}
    
    return result


# ============================================
# STEP 4: Generate Personalized Message
# ============================================

def generate_outreach_message(feed, producer_info, company_name):
    """Create a personalized BDR message"""
    
    host_name = producer_info.get("hosts", [{}])[0].get("name", "team").split()[0]
    
    prompt = f"""Write a short, personalized BDR outreach message.

Show: {feed.get('title')}
Host: {host_name}
Company: {company_name}

Tone: Professional but conversational. Not salesy. Focus on THEIR show's success.
Goal: Get them on a 20-min call to discuss audience growth strategies

Message requirements:
- 2-3 sentences max
- Reference something specific about their show
- Mention mowPod (podcast audience growth platform)
- Include a clear CTA for a call
- NO generic "let's jump on a call" language

Start with: "Hey [Host]," and be direct.

Just write the message. No preamble."""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=150,
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )
    
    return message.content[0].text


# ============================================
# STEP 5: Full Daily Run
# ============================================

def run_daily_bdr_scan():
    """Execute the full pipeline"""
    
    print(f"[{datetime.now()}] Starting BDR scan...")
    
    # Get recent feeds
    feeds = get_recent_podcast_feeds(hours=24, limit=500)
    print(f"Found {len(feeds)} new feeds")
    
    qualified_leads = []
    
    for feed in feeds:
        # Skip if not USA/CA/UK
        country = feed.get('country', '').upper()
        if country not in ['US', 'CA', 'UK']:
            continue
        
        # Classify
        classification = classify_brand_show(feed)
        
        if not classification.get("is_brand_show"):
            continue
        
        if classification.get("confidence", 0) < 0.6:  # Min confidence threshold
            continue
        
        print(f"✓ Qualified: {feed.get('title')} ({classification.get('confidence', 0):.0%})")
        
        # Extract producer info
        try:
            producer_info = extract_producer_info_from_website(
                feed.get("link"), 
                feed.get("title")
            )
        except Exception as e:
            print(f"  Warning: Could not extract from website - {e}")
            producer_info = {"hosts": [{"name": "Team"}], "company": "Unknown"}
        
        # Generate message
        message = generate_outreach_message(
            feed, 
            producer_info, 
            classification.get("company_name", "Unknown")
        )
        
        # Store
        lead = {
            "date_found": datetime.now().isoformat(),
            "show_title": feed.get("title"),
            "rss_feed": feed.get("feedUrl"),
            "website": feed.get("link"),
            "company": classification.get("company_name"),
            "hosts": producer_info.get("hosts"),
            "location": producer_info.get("location"),
            "classification_confidence": classification.get("confidence"),
            "outreach_message": message,
            "status": "ready_to_send"
        }
        
        qualified_leads.append(lead)
    
    # Save to file (or Airtable)
    output_file = f"bdr_leads_{datetime.now().strftime('%Y%m%d')}.json"
    with open(output_file, "w") as f:
        json.dump(qualified_leads, f, indent=2)
    
    print(f"\n✓ Found {len(qualified_leads)} qualified leads")
    print(f"✓ Saved to {output_file}")
    
    return qualified_leads


# Run it
if __name__ == "__main__":
    run_daily_bdr_scan()
