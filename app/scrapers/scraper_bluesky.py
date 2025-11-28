import pandas as pd
from atproto import Client
from dotenv import load_dotenv
import time, os
from app.utils.logger import get_logger
from app.cache.cache_manager import append_to_cache

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

# ---------- REGION LISTS ----------
UK_REGIONS = [
    "United Kingdom", "UK", "England", "Scotland", "Wales", "Northern Ireland",
    "Greater London", "Merseyside", "West Yorkshire", "South Yorkshire", "Kent",
    "Essex", "Surrey", "Hampshire", "Lancashire", "Cheshire", "Derbyshire",
    "Devon", "Cornwall", "Norfolk", "Suffolk", "Oxfordshire", "Cambridgeshire",
    "Warwickshire", "Staffordshire", "Nottinghamshire", "Leicestershire",
    "Gloucestershire", "Hertfordshire", "Buckinghamshire",
    "Aberdeenshire", "Glasgow", "Edinburgh", "Highland", "Dundee", "Fife",
    "Cardiff", "Swansea", "Newport", "Wrexham", "Flintshire", "Anglesey",
    "Antrim", "Armagh", "Down", "Fermanagh", "Londonderry", "Tyrone", "Belfast"
]

NIGERIA_REGIONS = [
    "Nigeria", "Nigerian", "Abia", "Adamawa", "Akwa Ibom", "Anambra",
    "Bauchi", "Bayelsa", "Benue", "Borno", "Cross River", "Delta", "Ebonyi",
    "Edo", "Ekiti", "Enugu", "Gombe", "Imo", "Jigawa", "Kaduna", "Kano",
    "Katsina", "Kebbi", "Kogi", "Kwara", "Lagos", "Nasarawa", "Niger",
    "Ogun", "Ondo", "Osun", "Oyo", "Plateau", "Rivers", "Sokoto",
    "Taraba", "Yobe", "Zamfara", "Abuja", "FCT"
]

# ---------- EXTRA KEYWORDS ----------
NIGERIA_KEYWORDS_EXTRA = [
    "efcc", "nfiu", "cbn", "icpc", "dss", "nafdac",
    "naira", "nasfat", "muric", "fomwan", "jaiz bank",
    "zakat foundation", "ummah support",
    "abuja", "lagos", "port harcourt", "arewa", "naija"
]

UK_KEYWORDS_EXTRA = [
    "charity commission", "hm treasury", "fca", "ofsi", "nca",
    "ukfiu", "necc", "hmrc",
    "pound sterling", "gbp", "uk banking",
    "national zakat foundation", "ummah welfare trust",
    "al-khair foundation", "islamic help", "human appeal",
    "london", "manchester", "birmingham", "leeds",
    "glasgow", "cardiff", "edinburgh"
]

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

def detect_location(text: str, bio: str, handle: str, display_name: str):
    """
    Detect location from post content, bio, handle, and display name.
    Returns: (country, region, confidence)
    """
    combined = " ".join([str(text), str(bio), str(handle), str(display_name)]).lower()
    country, region, confidence = None, None, "Low"

    # 1) Region-level detection (highest confidence)
    for r in NIGERIA_REGIONS:
        if r.lower() in combined:
            return "Nigeria", r, "High"
    for r in UK_REGIONS:
        if r.lower() in combined:
            return "UK", r, "High"

    # 2) Institutional/extra keyword detection (medium confidence)
    for kw in NIGERIA_KEYWORDS_EXTRA:
        if kw in combined:
            return "Nigeria", "Nigeria - Unknown", "Medium"
    for kw in UK_KEYWORDS_EXTRA:
        if kw in combined:
            return "UK", "UK - Unknown", "Medium"

    # 3) No detection (Low confidence, fallback)
    return country, region, confidence

def scrape_bluesky(keyword, max_posts=200, pause=2.0, enable_incremental_save=False, cache_type="csv", save_interval=50):
    """
    Scrape Bluesky posts with pagination, deduplication, and rate-limit compliance.
    - keyword: search term
    - max_posts: total posts to fetch
    - pause: seconds to wait between API calls (increased for better rate limit compliance)
    - enable_incremental_save: if True, saves data incrementally during scraping
    - cache_type: type of cache to use for incremental saves ('csv', 'sqlite', 'json')
    - save_interval: save to cache every N posts
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

                    # Location detection
                    country, region, confidence = detect_location(text, bio, author, display_name)
                    if country and not region:
                        region = f"{country} - Unknown"

                    data.append({
                        "keyword": keyword,
                        "uri": uri,
                        "author": author,
                        "display_name": display_name,
                        "did": did,
                        "text": text,
                        "created_at": created_at,
                        "bio": bio,
                        "country": country,
                        "region": region,
                        "confidence": confidence
                    })
                    batch_count += 1
                except Exception as post_error:
                    logger.warning(f"Failed to process individual post: {post_error}")
                    continue

            fetched += batch_count
            logger.info(f"Successfully fetched {batch_count} posts (total: {fetched})")

            # Incremental save if enabled
            if enable_incremental_save and len(data) >= save_interval:
                df_batch = pd.DataFrame(data)
                append_to_cache(df_batch, keyword, cache_type, platform="bluesky")
                logger.info(f"✅ Incrementally saved {len(data)} posts to cache")
                data = []  # Clear data after saving

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

    # Save any remaining data
    if enable_incremental_save and len(data) > 0:
        df_batch = pd.DataFrame(data)
        append_to_cache(df_batch, keyword, cache_type, platform="bluesky")
        logger.info(f"✅ Saved final {len(data)} posts to cache")

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
