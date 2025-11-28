from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse, FileResponse
from app.scrapers.scraper_factory import get_scraper
from app.cache.cache_manager import save_to_cache, load_from_cache
import os

router = APIRouter(prefix="/scrape", tags=["Scraping"])

def _scrape_platform(platform: str, keyword: str, limit: int, cache: str):
    """
    Generic helper function to scrape any platform with caching.
    """
    scraper = get_scraper(platform)

    if not scraper:
        return JSONResponse({"error": f"No scraper found for {platform}"}, status_code=404)

    # Check cache
    try:
        cached_df = load_from_cache(keyword, cache, platform)
        if cached_df is not None and not cached_df.empty:
            return JSONResponse(
                content={
                    "platform": platform,
                    "keyword": keyword,
                    "count": len(cached_df),
                    "data": cached_df.to_dict(orient="records"),
                    "message": f"Loaded {len(cached_df)} cached posts for '{keyword}' from {cache.upper()}."
                },
                status_code=200
            )
    except Exception as e:
        # Cache load failed, continue to fetch fresh data
        pass

    # Fetch fresh data
    try:
        df = scraper(keyword, limit)
        if df.empty:
            return JSONResponse(
                {
                    "message": f"No posts found for '{keyword}' on {platform}",
                    "platform": platform,
                    "keyword": keyword
                },
                status_code=200
            )

        # Save cache
        save_to_cache(df, keyword, cache, platform)

        return JSONResponse(
            content={
                "platform": platform,
                "keyword": keyword,
                "count": len(df),
                "data": df.to_dict(orient="records"),
                "message": f"Scraped {len(df)} posts for '{keyword}' and cached to {cache.upper()}."
            },
            status_code=200
        )
    except ValueError as e:
        # API key missing or invalid
        return JSONResponse(
            {"error": str(e), "platform": platform},
            status_code=400
        )
    except Exception as e:
        # Other errors
        return JSONResponse(
            {"error": f"Failed to scrape {platform}: {str(e)}"},
            status_code=500
        )


@router.get("/bluesky")
def scrape_bluesky(
    keyword: str = Query(..., description="Keyword or phrase to search on Bluesky", example="AgriTech"),
    limit: int = Query(50, ge=10, le=5000, description="Number of posts to fetch (10–5000)", example=50),
    cache: str = Query("sqlite", description="Cache type: 'csv', 'json', or 'sqlite'", example="sqlite"),
):
    """
    Scrape Bluesky posts, apply caching, and return results.
    """
    return _scrape_platform("bluesky", keyword, limit, cache)


@router.get("/reddit")
def scrape_reddit(
    keyword: str = Query(..., description="Keyword or phrase to search on Reddit", example="technology"),
    limit: int = Query(50, ge=10, le=5000, description="Number of posts to fetch (10–5000)", example=50),
    cache: str = Query("sqlite", description="Cache type: 'csv', 'json', or 'sqlite'", example="sqlite"),
):
    """
    Scrape Reddit posts, apply caching, and return results.
    """
    return _scrape_platform("reddit", keyword, limit, cache)


@router.get("/twitter")
def scrape_twitter(
    keyword: str = Query(..., description="Keyword or phrase to search on Twitter/X", example="AI"),
    limit: int = Query(50, ge=10, le=100, description="Number of tweets to fetch (10–100)", example=50),
    cache: str = Query("sqlite", description="Cache type: 'csv', 'json', or 'sqlite'", example="sqlite"),
):
    """
    Scrape Twitter/X posts, apply caching, and return results.
    """
    return _scrape_platform("twitter", keyword, limit, cache)


@router.get("/facebook")
def scrape_facebook(
    keyword: str = Query(..., description="Keyword or phrase to search on Facebook", example="climate"),
    limit: int = Query(50, ge=10, le=5000, description="Number of posts to fetch (10–5000)", example=50),
    cache: str = Query("sqlite", description="Cache type: 'csv', 'json', or 'sqlite'", example="sqlite"),
):
    """
    Scrape Facebook posts, apply caching, and return results.
    """
    return _scrape_platform("facebook", keyword, limit, cache)


@router.get("/news")
def scrape_news(
    keyword: str = Query(..., description="Keyword or phrase to search news articles", example="cybersecurity"),
    limit: int = Query(50, ge=10, le=100, description="Number of articles to fetch (10–100)", example=50),
    cache: str = Query("sqlite", description="Cache type: 'csv', 'json', or 'sqlite'", example="sqlite"),
):
    """
    Scrape news articles, apply caching, and return results.
    """
    return _scrape_platform("news", keyword, limit, cache)


@router.get("/export")
def export_cache(
    platform: str = Query("bluesky", description="Platform to export (bluesky, reddit, twitter, facebook, news)", example="bluesky"),
    keyword: str = Query(None, description="Specific keyword to export (if None, exports merged dataset)", example="FATF"),
    format: str = Query("csv", description="Export format: csv, json, or sqlite", example="csv")
):
    """
    Export cached dataset for a specific platform and keyword, or the final merged dataset.

    - If keyword is provided: exports that specific keyword's cache
    - If keyword is None: looks for final merged dataset (bluesky_ctf_dataset.csv, etc.)
    """
    from app.cache.cache_manager import _cache_path, CACHE_DIR

    if keyword:
        # Export specific keyword cache
        file_path = _cache_path(keyword, format, platform)
    else:
        # Export final merged dataset (look in root directory)
        output_files = {
            "csv": f"{platform}_ctf_dataset.csv",
            "json": f"{platform}_ctf_dataset.json",
            "sqlite": f"{platform}_ctf_dataset.db"
        }
        file_path = output_files.get(format, f"{platform}_ctf_dataset.csv")

    if not os.path.exists(file_path):
        # Try to find any available cache files for this platform
        import glob
        available_files = glob.glob(f"{CACHE_DIR}/{platform}_*.{format}")

        if available_files:
            return JSONResponse({
                "error": f"No cache found at {file_path}",
                "available_files": [os.path.basename(f) for f in available_files],
                "hint": "Use the keyword parameter to export a specific keyword cache, or run the scraper first to generate the merged dataset."
            }, status_code=404)
        else:
            return JSONResponse({
                "error": f"No {format.upper()} cache found for platform '{platform}'",
                "hint": "Run the scraper first to generate cached data."
            }, status_code=404)

    media_type = {
        "csv": "text/csv",
        "json": "application/json",
        "sqlite": "application/octet-stream"
    }[format]

    return FileResponse(file_path, media_type=media_type, filename=os.path.basename(file_path))


@router.get("/export/list")
def list_cached_files(
    platform: str = Query(None, description="Filter by platform (bluesky, reddit, twitter, facebook, news)", example="bluesky")
):
    """
    List all available cached files, optionally filtered by platform.
    """
    from app.cache.cache_manager import CACHE_DIR
    import glob

    if platform:
        pattern = f"{CACHE_DIR}/{platform}_*"
    else:
        pattern = f"{CACHE_DIR}/*"

    files = glob.glob(pattern)

    file_info = []
    for file_path in files:
        filename = os.path.basename(file_path)
        size = os.path.getsize(file_path)

        # Parse platform and keyword from filename
        # Format: platform_keyword.extension
        parts = filename.rsplit('.', 1)
        name_part = parts[0]
        extension = parts[1] if len(parts) > 1 else ''

        if '_' in name_part:
            file_platform, keyword = name_part.split('_', 1)
        else:
            file_platform = name_part
            keyword = ''

        file_info.append({
            "filename": filename,
            "platform": file_platform,
            "keyword": keyword.replace('_', ' '),
            "format": extension,
            "size_bytes": size,
            "size_kb": round(size / 1024, 2)
        })

    return JSONResponse({
        "total_files": len(file_info),
        "files": file_info
    })


