import pandas as pd
import praw
from dotenv import load_dotenv
import os

load_dotenv()

# Reddit API credentials
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "Social Scraper API v2.0")

def scrape_reddit(keyword, max_posts=200):
    """
    Scrape Reddit posts using PRAW (Python Reddit API Wrapper).
    - keyword: search term or subreddit topic
    - max_posts: total posts to fetch
    """
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )

    data = []

    # Search across all of Reddit
    for submission in reddit.subreddit("all").search(keyword, limit=max_posts):
        data.append({
            "keyword": keyword,
            "post_id": submission.id,
            "title": submission.title,
            "text": submission.selftext,
            "author": str(submission.author),
            "subreddit": str(submission.subreddit),
            "score": submission.score,
            "num_comments": submission.num_comments,
            "created_at": pd.to_datetime(submission.created_utc, unit='s'),
            "url": submission.url,
            "permalink": f"https://reddit.com{submission.permalink}"
        })

    df = pd.DataFrame(data)
    if "post_id" in df.columns:
        df = df.drop_duplicates(subset=["post_id"])
    return df
