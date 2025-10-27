from fastapi import FastAPI
from app.routes.scrape_routes import router as scrape_router

app = FastAPI(title="Social Scraper API", version="2.0")
app.include_router(scrape_router)

@app.get("/")
def root():
    return {"message": "Welcome to the Social Scraper API"}
