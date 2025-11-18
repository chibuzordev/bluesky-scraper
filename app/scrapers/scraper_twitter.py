import pandas as pd
import tweepy
from dotenv import load_dotenv
import os

load_dotenv()

# X/Twitter API credentials (v2)
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

def scrape_twitter(keyword, max_posts=200):
    """
    Scrape X/Twitter posts using Tweepy with API v2.
    - keyword: search term
    - max_posts: total tweets to fetch
    """
    client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN)

    data = []

    # Search recent tweets
    tweets = client.search_recent_tweets(
        query=keyword,
        max_results=min(100, max_posts),  # API max is 100 per request
        tweet_fields=['created_at', 'public_metrics', 'author_id', 'lang'],
        user_fields=['username', 'name', 'description'],
        expansions=['author_id']
    )

    if not tweets.data:
        return pd.DataFrame()

    # Create user lookup dictionary
    users = {user.id: user for user in tweets.includes.get('users', [])}

    for tweet in tweets.data:
        author = users.get(tweet.author_id)

        data.append({
            "keyword": keyword,
            "tweet_id": tweet.id,
            "text": tweet.text,
            "author_id": tweet.author_id,
            "author_username": author.username if author else None,
            "author_name": author.name if author else None,
            "author_bio": author.description if author else None,
            "created_at": tweet.created_at,
            "retweet_count": tweet.public_metrics.get('retweet_count', 0),
            "reply_count": tweet.public_metrics.get('reply_count', 0),
            "like_count": tweet.public_metrics.get('like_count', 0),
            "quote_count": tweet.public_metrics.get('quote_count', 0),
            "language": tweet.lang,
            "url": f"https://twitter.com/i/web/status/{tweet.id}"
        })

    df = pd.DataFrame(data)
    if "tweet_id" in df.columns:
        df = df.drop_duplicates(subset=["tweet_id"])
    return df
