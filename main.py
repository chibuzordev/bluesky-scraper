from fastapi import FastAPI, Query
from scraper import scrape_bluesky

app = FastAPI(title="Bluesky AML/CTF Scraper API", version="1.0")

@app.get("/")
def root():
    return {"message": "Welcome to the Bluesky AML/CTF Scraper API"}

@app.get("/scrape")
def scrape(keyword: str = Query(..., description="Keyword to search for"),
           limit: int = Query(50, ge=10, le=500, description="Number of posts to fetch")):
    """
    Trigger a Bluesky scrape by keyword.
    """
    df = scrape_bluesky(keyword, limit)
    return {
        "keyword": keyword,
        "count": len(df),
        "message": f"Scraped {len(df)} posts for keyword '{keyword}'.",
    }
