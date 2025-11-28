import pandas as pd
import os
import sqlite3
import json
from datetime import datetime
from app.utils.logger import get_logger

logger = get_logger()

CACHE_DIR = "app/cache/cached_files"
CHECKPOINT_DIR = "app/cache/checkpoints"
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(CHECKPOINT_DIR, exist_ok=True)

def _cache_path(keyword, cache_type, platform):
    base_name = f"{platform}_{keyword.replace(' ', '_').lower()}"
    return os.path.join(CACHE_DIR, f"{base_name}.{cache_type}")

def _checkpoint_path(session_name, platform):
    """Get path for checkpoint file."""
    return os.path.join(CHECKPOINT_DIR, f"{platform}_{session_name}_checkpoint.json")

def save_to_cache(df, keyword, cache_type="sqlite", platform="bluesky"):
    """Save DataFrame to cache."""
    if df is None or df.empty:
        logger.warning(f"Attempted to save empty DataFrame for keyword '{keyword}'")
        return

    path = _cache_path(keyword, cache_type, platform)

    try:
        if cache_type == "csv":
            df.to_csv(path, index=False)
        elif cache_type == "json":
            df.to_json(path, orient="records", indent=2)
        elif cache_type == "sqlite":
            conn = sqlite3.connect(path)
            df.to_sql("posts", conn, if_exists="replace", index=False)
            conn.close()
        else:
            raise ValueError("Unsupported cache type. Use 'csv', 'json', or 'sqlite'.")

        logger.info(f"Saved {len(df)} posts to cache: {path}")
    except Exception as e:
        logger.error(f"Failed to save to cache: {e}")

def append_to_cache(df, keyword, cache_type="csv", platform="bluesky"):
    """
    Append new data to existing cache (incremental saving).
    For CSV: appends to file
    For SQLite: merges and deduplicates by 'uri'
    """
    if df is None or df.empty:
        return

    path = _cache_path(keyword, cache_type, platform)

    try:
        if cache_type == "csv":
            # Append to CSV
            if os.path.exists(path):
                df.to_csv(path, mode='a', header=False, index=False)
                logger.info(f"Appended {len(df)} posts to {path}")
            else:
                df.to_csv(path, index=False)
                logger.info(f"Created new cache file with {len(df)} posts: {path}")

        elif cache_type == "sqlite":
            # Load existing, merge, deduplicate
            existing_df = load_from_cache(keyword, cache_type, platform)
            if existing_df is not None and not existing_df.empty:
                combined = pd.concat([existing_df, df], ignore_index=True)
                if 'uri' in combined.columns:
                    combined = combined.drop_duplicates(subset=['uri'], keep='last')
                logger.info(f"Merged {len(df)} new posts with {len(existing_df)} existing (total: {len(combined)})")
            else:
                combined = df
                logger.info(f"Created new cache with {len(combined)} posts")

            conn = sqlite3.connect(path)
            combined.to_sql("posts", conn, if_exists="replace", index=False)
            conn.close()

        elif cache_type == "json":
            # Load existing, merge, deduplicate
            existing_df = load_from_cache(keyword, cache_type, platform)
            if existing_df is not None and not existing_df.empty:
                combined = pd.concat([existing_df, df], ignore_index=True)
                if 'uri' in combined.columns:
                    combined = combined.drop_duplicates(subset=['uri'], keep='last')
            else:
                combined = df

            combined.to_json(path, orient="records", indent=2)

    except Exception as e:
        logger.error(f"Failed to append to cache: {e}")

def load_from_cache(keyword, cache_type="sqlite", platform="bluesky"):
    """Load DataFrame from cache."""
    path = _cache_path(keyword, cache_type, platform)

    if not os.path.exists(path):
        return None

    try:
        if cache_type == "csv":
            return pd.read_csv(path)
        elif cache_type == "json":
            return pd.read_json(path)
        elif cache_type == "sqlite":
            conn = sqlite3.connect(path)
            df = pd.read_sql("SELECT * FROM posts", conn)
            conn.close()
            return df
    except Exception as e:
        logger.error(f"Failed to load from cache: {e}")
        return None

def save_checkpoint(session_name, completed_keywords, platform="bluesky", metadata=None):
    """Save checkpoint of completed keywords."""
    checkpoint = {
        "session_name": session_name,
        "platform": platform,
        "completed_keywords": completed_keywords,
        "last_updated": datetime.now().isoformat(),
        "metadata": metadata or {}
    }

    path = _checkpoint_path(session_name, platform)
    try:
        with open(path, 'w') as f:
            json.dump(checkpoint, f, indent=2)
        logger.info(f"Saved checkpoint: {len(completed_keywords)} keywords completed")
    except Exception as e:
        logger.error(f"Failed to save checkpoint: {e}")

def load_checkpoint(session_name, platform="bluesky"):
    """Load checkpoint of completed keywords."""
    path = _checkpoint_path(session_name, platform)

    if not os.path.exists(path):
        return None

    try:
        with open(path, 'r') as f:
            checkpoint = json.load(f)
        logger.info(f"Loaded checkpoint: {len(checkpoint.get('completed_keywords', []))} keywords completed")
        return checkpoint
    except Exception as e:
        logger.error(f"Failed to load checkpoint: {e}")
        return None

def merge_all_caches(keywords, output_file, cache_type="csv", platform="bluesky"):
    """Merge all cached keyword results into a single output file."""
    all_dfs = []

    for keyword in keywords:
        df = load_from_cache(keyword, cache_type, platform)
        if df is not None and not df.empty:
            all_dfs.append(df)
            logger.info(f"Loaded {len(df)} posts for keyword '{keyword}'")

    if not all_dfs:
        logger.warning("No cached data found to merge")
        return None

    # Combine all DataFrames
    combined = pd.concat(all_dfs, ignore_index=True)

    # Deduplicate by URI
    if 'uri' in combined.columns:
        initial_count = len(combined)
        combined = combined.drop_duplicates(subset=['uri'])
        logger.info(f"Deduplication: {initial_count} -> {len(combined)} posts")

    # Save to output file
    try:
        combined.to_csv(output_file, index=False)
        logger.info(f"Merged dataset saved to {output_file}: {len(combined)} unique posts")
        return combined
    except Exception as e:
        logger.error(f"Failed to save merged dataset: {e}")
        return None

