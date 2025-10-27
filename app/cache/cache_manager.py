import pandas as pd
import os
import sqlite3
import json

CACHE_DIR = "app/cache/cached_files"
os.makedirs(CACHE_DIR, exist_ok=True)

def _cache_path(keyword, cache_type, platform):
    base_name = f"{platform}_{keyword.replace(' ', '_').lower()}"
    return os.path.join(CACHE_DIR, f"{base_name}.{cache_type}")


def save_to_cache(df, keyword, cache_type="sqlite", platform="bluesky"):
    path = _cache_path(keyword, cache_type, platform)

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


def load_from_cache(keyword, cache_type="sqlite", platform="bluesky"):
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
    except Exception:
        return None
