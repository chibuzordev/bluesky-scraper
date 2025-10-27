### Blue Sky Scraper

A lightweight, modular FastAPI service for collecting and analyzing social and institutional data across Bluesky.

##### Overview

The Social Data Intelligence API enables you to collect text-based data from public online platforms. With keyword-based searches and retrieve clean, structured datasets, the results will be saved incrementally to avoid data loss. The methods used maintain compliance with rate limits and pagination controls that can be extended to new sources using a unified schema.

It’s built for researchers, analysts, and developers who need quick access to social discourse data for analytics, monitoring, or policy intelligence.

The system supports:
- keyword searches for profiles and 'skeets' 
- smart pagination & rate Limiting backed by deduplication & incremental Saving
- modular and deployment as a microservice or standalone backend via FastAPI
```
social_scraper/
│
├── app/
│   ├── __init__.py
│   ├── main.py                 # Entry point (FastAPI app)
│   ├── routes/
│   │   ├── __init__.py
│   │   └── scrape_routes.py    # Contains API route logic (optional modularity)
│   │
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── scraper_bluesky.py  # Bluesky scraper
│   │   ├── scraper_reddit.py   # Reddit scraper (to be added)
│   │   └── scraper_factory.py  # Returns scraper dynamically
│   │
│   ├── cache/
│   │   ├── __init__.py
│   │   └── cache_manager.py    # Cache system for csv/json/sqlite
│   │
│   └── utils/
│       ├── __init__.py
│       └── logger.py           # (optional) unified logging system
│
├── .env                        # Environment variables (API keys, credentials)
├── requirements.txt            # Dependencies
├── Dockerfile
├── render.yaml                 # Render deployment config (optional)
└── README.md
```


| Layer              | Purpose                                                                  |
| ------------------ | ------------------------------------------------------------------------ |
| `app/main.py`      | Entry point of the FastAPI server                                        |
| `app/scrapers/`    | Contains scraper implementations (one file per platform)                 |
| `app/cache/`       | Handles caching & persistence for all platforms                          |
| `app/routes/`      | Keeps route logic clean and modular (optional if you prefer fewer files) |
| `app/utils/`       | For shared logic such as logging, formatting, or error handling          |
| `.env`             | Keeps credentials & settings out of code                                 |
| `requirements.txt` | Lists all dependencies for local, Docker, or Render builds               |
| `render.yaml`      | Automates Render deployment                                              |
| `Dockerfile`       | Ensures reproducible build & deployment environment                      |
