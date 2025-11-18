from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse, FileResponse
from app.scrapers.scraper_factory import get_scraper
from app.cache.cache_manager import save_to_cache, load_from_cache
import os

router = APIRouter(prefix="/scrape", tags=["Scraping"])

@router.get("/bluesky")
def scrape_bluesky(
    keyword: str = Query(..., description="Keyword or phrase to search on Bluesky", example="AgriTech"),
    limit: int = Query(50, ge=10, le=500, description="Number of posts to fetch (10–500)", example=50),
    cache: str = Query("sqlite", description="Cache type: 'csv', 'json', or 'sqlite'", example="sqlite"),
):
    """
    Scrape Bluesky posts, apply caching, and return results.
    """
    platform = "bluesky"
    scraper = get_scraper(platform)

    if not scraper:
        return JSONResponse({"error": f"No scraper found for {platform}"}, status_code=404)

    # Check cache
    cached_df = load_from_cache(keyword, cache)
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

    # Fetch fresh data
    df = scraper(keyword, limit)
    if df.empty:
        return JSONResponse({"message": "No posts found"}, status_code=200)

    # Save cache
    save_to_cache(df, keyword, cache)

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


@router.get("/export")
def export_cache(
    format: str = Query("csv", description="Export format: csv, json, or sqlite", example="csv")
):
    """
    Export cached dataset in the specified format.
    """
    file_map = {
        "csv": "cache/bluesky_cache.csv",
        "json": "cache/bluesky_cache.json",
        "sqlite": "cache/bluesky_cache.db"
    }

    path = file_map.get(format)
    if not path or not os.path.exists(path):
        return JSONResponse({"message": f"No {format.upper()} cache found."}, status_code=404)

    media_type = {
        "csv": "text/csv",
        "json": "application/json",
        "sqlite": "application/octet-stream"
    }[format]

    return FileResponse(path, media_type=media_type, filename=os.path.basename(path))

