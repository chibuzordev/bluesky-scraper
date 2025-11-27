import pandas as pd
from atproto import Client
from dotenv import load_dotenv
import time, os
from app.utils.logger import get_logger

# ✅ ensure pandas shows full text
pd.set_option("display.max_colwidth", None)

# Load environment variables
load_dotenv()

# Get logger
logger = get_logger()

# Retrieve credentials and settings
USERNAME = os.getenv("BLUESKY_USERNAME")
APP_PASSWORD = os.getenv("BLUESKY_APP_PASSWORD")
LIMIT = int(os.getenv("BLUESKY_LIMIT", 50))  # fallback to 50 if missing
OUTPUT_FILE = os.getenv("BLUESKY_OUTPUT_FILE", "bluesky_ctf_dataset.csv")

# Initialize client (will login on first use)
client = None

def get_client():
    """Initialize and return authenticated Bluesky client."""
    global client
    if client is None:
        client = Client()
        try:
            client.login(USERNAME, APP_PASSWORD)
            logger.info(f"Successfully logged in as {USERNAME}")
        except Exception as e:
            logger.error(f"Failed to login to Bluesky: {e}")
            raise ValueError(f"Bluesky authentication failed: {e}")
    return client

def scrape_bluesky(keyword, max_posts=200, pause=2.0):
    """
    Scrape Bluesky posts with pagination, deduplication, and rate-limit compliance.
    - keyword: search term
    - max_posts: total posts to fetch
    - pause: seconds to wait between API calls (increased for better rate limit compliance)
    """
    logger.info(f"Starting Bluesky scrape for keyword: '{keyword}', max_posts: {max_posts}")

    try:
        client = get_client()
    except Exception as e:
        logger.error(f"Client initialization failed: {e}")
        raise

    data = []
    cursor = None
    fetched = 0
    batch_size = 25  # Reduced from 50 to be more conservative with API limits
    consecutive_errors = 0
    max_consecutive_errors = 3

    while fetched < max_posts:
        try:
            # Calculate how many posts to request in this batch
            remaining = max_posts - fetched
            current_limit = min(batch_size, remaining)

            params = {"q": keyword, "limit": current_limit}
            if cursor:
                params["cursor"] = cursor

            logger.info(f"Fetching batch: {fetched}/{max_posts} posts (limit={current_limit}, cursor={'yes' if cursor else 'no'})")

            # Make API request
            results = client.app.bsky.feed.search_posts(params)

            # Check if we got any posts
            if not results.posts:
                logger.info("No more posts found, stopping pagination")
                break

            # Process each post
            batch_count = 0
            for post in results.posts:
                try:
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
                    batch_count += 1
                except Exception as post_error:
                    logger.warning(f"Failed to process individual post: {post_error}")
                    continue

            fetched += batch_count
            logger.info(f"Successfully fetched {batch_count} posts (total: {fetched})")

            # Reset error counter on success
            consecutive_errors = 0

            # Check for next page cursor
            cursor = getattr(results, "cursor", None)
            if not cursor:
                logger.info("No cursor returned, reached end of results")
                break

            # Rate limiting pause
            if fetched < max_posts:
                logger.info(f"Waiting {pause}s before next request...")
                time.sleep(pause)

        except Exception as e:
            consecutive_errors += 1
            logger.error(f"Error during pagination (attempt {consecutive_errors}/{max_consecutive_errors}): {e}")

            if consecutive_errors >= max_consecutive_errors:
                logger.error(f"Too many consecutive errors, stopping scrape. Collected {fetched} posts so far.")
                break

            # Wait longer before retrying
            logger.info(f"Waiting {pause * 2}s before retrying...")
            time.sleep(pause * 2)

    # Create DataFrame and deduplicate
    logger.info(f"Creating DataFrame from {len(data)} posts")
    df = pd.DataFrame(data)

    if len(df) > 0 and "uri" in df.columns:
        initial_count = len(df)
        df = df.drop_duplicates(subset=["uri"])
        duplicates_removed = initial_count - len(df)
        if duplicates_removed > 0:
            logger.info(f"Removed {duplicates_removed} duplicate posts")

    logger.info(f"Scrape completed. Returning {len(df)} unique posts")
    return df
