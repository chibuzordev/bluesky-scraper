import pandas as pd
import requests
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import logging

load_dotenv()

logger = logging.getLogger("social_scraper")

# NewsAPI credentials
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

def scrape_news(keyword, max_posts=200):
    """
    Scrape news articles using NewsAPI.
    - keyword: search term
    - max_posts: total articles to fetch (max 100 on free tier)
    """
    if not NEWS_API_KEY:
        logger.error("NEWS_API_KEY not found in environment variables")
        raise ValueError("NEWS_API_KEY is required. Please add it to your .env file")

    base_url = "https://newsapi.org/v2/everything"

    # Calculate date range (last 7 days for better results on free tier)
    to_date = datetime.now()
    from_date = to_date - timedelta(days=7)

    params = {
        "q": keyword,
        "apiKey": NEWS_API_KEY,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": min(100, max_posts),  # NewsAPI free tier max is 100
        "from": from_date.strftime("%Y-%m-%d"),
        "to": to_date.strftime("%Y-%m-%d")
    }

    data = []

    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()

        result = response.json()

        # Check for API errors
        if result.get("status") == "error":
            error_msg = result.get("message", "Unknown error")
            logger.error(f"NewsAPI Error: {error_msg}")
            raise ValueError(f"NewsAPI Error: {error_msg}")

        articles = result.get("articles", [])
        logger.info(f"NewsAPI returned {len(articles)} articles for keyword '{keyword}'")

        if not articles:
            logger.warning(f"No articles found for keyword '{keyword}'")
            return pd.DataFrame()

        for article in articles:
            # Skip articles with removed content
            if article.get("title") == "[Removed]":
                continue

            data.append({
                "keyword": keyword,
                "title": article.get("title"),
                "description": article.get("description"),
                "content": article.get("content"),
                "author": article.get("author"),
                "source_name": article.get("source", {}).get("name"),
                "source_id": article.get("source", {}).get("id"),
                "published_at": article.get("publishedAt"),
                "url": article.get("url"),
                "image_url": article.get("urlToImage")
            })

    except requests.exceptions.RequestException as e:
        logger.error(f"NewsAPI Request Error: {e}")
        raise ValueError(f"Failed to fetch news: {str(e)}")

    df = pd.DataFrame(data)
    if "url" in df.columns and not df.empty:
        df = df.drop_duplicates(subset=["url"])

    logger.info(f"Returning {len(df)} news articles after deduplication")
    return df
