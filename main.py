from fastapi import FastAPI, Query
from scraper import scrape_bluesky
from fastapi.responses import JSONResponse

app = FastAPI(title="Bluesky AML/CTF Scraper API", version="1.1")

@app.get("/")
def root():
    return {"message": "Welcome to the Bluesky AML/CTF Scraper API"}

@app.get("/scrape")
def scrape(
    keyword: str = Query(..., description="Keyword to search for"),
    limit: int = Query(50, ge=10, le=500, description="Number of posts to fetch")
):
    """
    Trigger a Bluesky scrape by keyword and return the post data.
    """
    df = scrape_bluesky(keyword, limit)

    if df.empty:
        return JSONResponse(
            content={"keyword": keyword, "count": 0, "message": "No posts found."},
            status_code=200
        )

    # Convert DataFrame to list of dictionaries for JSON output
    data = df.to_dict(orient="records")

    return JSONResponse(
        content={
            "keyword": keyword,
            "count": len(df),
            "data": data,
            "message": f"Scraped {len(df)} posts for keyword '{keyword}'."
        },
        status_code=200
    )
