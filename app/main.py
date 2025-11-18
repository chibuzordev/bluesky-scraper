from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.scrape_routes import router as scrape_router

app = FastAPI(title="Social Scraper API", version="2.0")

# CORS middleware (allow all during development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # during development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scrape_router)

@app.get("/")
def root():
    return {"message": "Welcome to the Social Scraper API"}

