from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, FileResponse
from scraper_factory import get_scraper
from cache_manager import save_to_cache, load_from_cache
import os, time

app = FastAPI(
    title="Social Media Scraper API",
    version="3.0",
    description="Unified scraper for multiple social media sources (Bluesky, Reddit, etc.)"
)

# ✅ Root route
@app.get("/")
def root():
    return {
        "message": "Welcome to the Social Media Scraper API",
        "available_endpoints": ["/scrape", "/export"],
        "supported_platforms": ["bluesky", "reddit"],  # expandable
    }


# ✅ Unified Scrape Endpoint
@app.get("/scrape")
def scrape(
    platform: str = Query(..., description="Social platform (e.g., 'bluesky', 'reddit')", example="bluesky"),
    keyword: str = Query(..., description="Keyword or phrase to search", example="AgriTech"),
    limit: int = Query(50, ge=10, le=500, description="Number of posts to fetch", example=50),
    cache: str = Query("sqlite", description="Cache type: 'csv', 'json', or 'sqlite'", example="sqlite"),
):
    """
    Scrape data from a specified social media platform.
    Automatically caches results for reuse across future requests.
    """
    # Load existing cache
    cached_df = load_from_cache(keyword, cache, platform)
    if cached_df is not None and not cached_df.empty:
        return JSONResponse(
            content={
                "platform": platform,
                "keyword": keyword,
                "count": len(cached_df),
                "data": cached_df.to_dict(orient="records"),
                "message": f"Loaded {len(cached_df)} cached posts for '{keyword}' on {platform.title()} from {cache.upper()}."
            },
            status_code=200
        )

    # Get the appropriate scraper dynamically
    scraper = get_scraper(platform)
    if scraper is None:
        return JSONResponse(
            {"error": f"Unsupported platform '{platform}'. Supported: bluesky, reddit."},
            status_code=400
        )

    # Fetch fresh data
    df = scraper(keyword, limit)
    if df.empty:
        return JSONResponse(
            {"message": f"No posts found for '{keyword}' on {platform.title()}."},
            status_code=200
        )

    # Save to cache
    save_to_cache(df, keyword, cache, platform)

    return JSONResponse(
        content={
            "platform": platform,
            "keyword": keyword,
            "count": len(df),
            "data": df.to_dict(orient="records"),
            "message": f"Scraped {len(df)} posts for '{keyword}' on {platform.title()} and cached to {cache.upper()}."
        },
        status_code=200
    )


# ✅ Export cached data
@app.get("/export")
def export(
    platform: str = Query("bluesky", description="Platform to export data for", example="bluesky"),
    format: str = Query("csv", description="Export format: csv, json, or sqlite", example="csv")
):
    """
    Export cached dataset in the specified format and platform.
    """
    path = f"cache/{platform}_cache.{format}"

    if not os.path.exists(path):
        return JSONResponse(
            {"message": f"No {format.upper()} cache found for {platform.title()}."},
            status_code=404
        )

    media_types = {
        "csv": "text/csv",
        "json": "application/json",
        "sqlite": "application/octet-stream",
    }

    return FileResponse(
        path,
        media_type=media_types.get(format, "application/octet-stream"),
        filename=os.path.basename(path)
    )
