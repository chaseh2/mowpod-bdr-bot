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
        
        print(f"Fetching from Podcast Index...")
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"API Error: {response.text[:500]}")
            return []
        
        data = response.json()
        feeds = data.get("feeds", [])
        print(f"✓ Got {len(feeds)} feeds")
        return feeds
        
    except Exception as e:
        print(f"ERROR fetching feeds: {e}")
        return []
