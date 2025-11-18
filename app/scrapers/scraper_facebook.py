import pandas as pd
import requests
from dotenv import load_dotenv
import os

load_dotenv()

# Facebook Graph API credentials
FACEBOOK_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")
FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")  # Optional: specific page to scrape

def scrape_facebook(keyword, max_posts=200):
    """
    Scrape Facebook posts using Graph API.
    Note: Facebook's API has strict limitations. This searches posts from a specific page.
    For broader search, you need approved access to search endpoints.
    - keyword: search term (used to filter posts)
    - max_posts: total posts to fetch
    """
    if not FACEBOOK_ACCESS_TOKEN:
        return pd.DataFrame()

    base_url = "https://graph.facebook.com/v21.0"
    data = []

    # If page ID is provided, search that page's posts
    if FACEBOOK_PAGE_ID:
        url = f"{base_url}/{FACEBOOK_PAGE_ID}/posts"
        params = {
            "access_token": FACEBOOK_ACCESS_TOKEN,
            "fields": "id,message,created_time,permalink_url,shares,likes.summary(true),comments.summary(true)",
            "limit": min(100, max_posts)
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            posts = response.json().get("data", [])

            for post in posts:
                # Filter by keyword if message exists
                message = post.get("message", "")
                if keyword.lower() not in message.lower():
                    continue

                data.append({
                    "keyword": keyword,
                    "post_id": post.get("id"),
                    "message": message,
                    "created_at": post.get("created_time"),
                    "permalink": post.get("permalink_url"),
                    "shares": post.get("shares", {}).get("count", 0),
                    "likes": post.get("likes", {}).get("summary", {}).get("total_count", 0),
                    "comments": post.get("comments", {}).get("summary", {}).get("total_count", 0)
                })

        except requests.exceptions.RequestException as e:
            print(f"Facebook API Error: {e}")
            return pd.DataFrame()

    df = pd.DataFrame(data)
    if "post_id" in df.columns:
        df = df.drop_duplicates(subset=["post_id"])
    return df
