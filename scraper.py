import pandas as pd
from atproto import Client
from dotenv import load_dotenv
import time, os

# ✅ ensure pandas shows full text
pd.set_option("display.max_colwidth", None)

# Load environment variables
load_dotenv()

# Retrieve credentials and settings
USERNAME = os.getenv("BLUESKY_USERNAME")
APP_PASSWORD = os.getenv("BLUESKY_APP_PASSWORD")
LIMIT = int(os.getenv("BLUESKY_LIMIT", 50))  # fallback to 50 if missing
OUTPUT_FILE = os.getenv("BLUESKY_OUTPUT_FILE", "bluesky_ctf_dataset.csv")

client = Client()
client.login(USERNAME, APP_PASSWORD)

def scrape_bluesky(keyword, max_posts=200, pause=1.5):
    """
    Scrape Bluesky posts with pagination, deduplication, and rate-limit compliance.
    - keyword: search term
    - max_posts: total posts to fetch
    - pause: seconds to wait between API calls
    """
    data = []
    cursor = None
    fetched = 0
    batch_size = 50  # API max per request is 100

    while fetched < max_posts:
        params = {"q": keyword, "limit": min(batch_size, max_posts - fetched)}
        if cursor:
            params["cursor"] = cursor

        results = client.app.bsky.feed.search_posts(params)
        if not results.posts:
            break

        for post in results.posts:
            author = post.author.handle
            display_name = getattr(post.author, "display_name", None)
            did = getattr(post.author, "did", None)
            text = getattr(post.record, "text", "")
            created_at = getattr(post.record, "created_at", None)
            bio = getattr(post.author, "description", None)
            uri = getattr(post, "uri", None)


            data.append({
                "keyword": keyword,
                "uri": uri,
                "author": author,
                "display_name": display_name,
                "did": did,
                "text": text,
                "created_at": created_at,
                "bio": bio
            })

        cursor = getattr(results, "cursor", None)
        fetched += len(results.posts)

        if not cursor:
            break

        time.sleep(pause)

    df = pd.DataFrame(data)
    if "uri" in df.columns:
        df = df.drop_duplicates(subset=["uri"])
    return df