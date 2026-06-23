import os
import requests
import anthropic

print("=== Testing APIs ===\n")

# Test Anthropic
print("1. Testing Anthropic...")
try:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    msg = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=50,
        messages=[{"role": "user", "content": "Say hello"}]
    )
    print("✓ Anthropic works\n")
except Exception as e:
    print(f"✗ Anthropic failed: {e}\n")

# Test Podcast Index
print("2. Testing Podcast Index...")
try:
    api_key = os.getenv("PODCASTINDEX_API_KEY")
    if not api_key:
        print("✗ PODCASTINDEX_API_KEY not set\n")
    else:
        url = "https://api.podcastindex.org/api/1.0/feeds/recent"
        headers = {
            "User-Agent": "mowPod-BDR-Bot",
            "X-Podcastindex-Auth": api_key
        }
        response = requests.get(url, headers=headers, params={"max": 5})
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Got {len(data.get('feeds', []))} feeds\n")
        else:
            print(f"✗ API error\n")
except Exception as e:
    print(f"✗ Podcast Index failed: {e}\n")
