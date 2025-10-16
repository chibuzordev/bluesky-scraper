### Blue Sky Scraper

A lightweight, modular FastAPI service for collecting and analyzing social and institutional data across Bluesky.

##### Overview

The Social Data Intelligence API enables you to collect text-based data from public online platforms. With keyword-based searches and retrieve clean, structured datasets, the results will be saved incrementally to avoid data loss. The methods used maintain compliance with rate limits and pagination controls that can be extended to new sources using a unified schema.

It’s built for researchers, analysts, and developers who need quick access to social discourse data for analytics, monitoring, or policy intelligence.

The system supports:
- keyword searches for profiles and 'skeets' 
- smart pagination & rate Limiting backed by deduplication & incremental Saving
- modular and deployment as a microservice or standalone backend via FastAPI
