### Blue Sky Scraper

A lightweight, modular FastAPI service for collecting and analyzing social and institutional data across multiple platforms. It starts with Bluesky, and is extendable to Twitter/X, YouTube, News, and more.

##### Overview

The Social Data Intelligence API enables you to collect text-based data from public online platforms. With keyword-based searches and retrieve clean, structured datasets, the results will be saved incrementally to avoid data loss. The methods used maintain compliance with rate limits and pagination controls that can be extended to new sources using a unified schema.

It’s built for researchers, analysts, and developers who need quick access to social discourse data for analytics, monitoring, or policy intelligence.

##### Key Features
- 🔍 Multi-Platform Ready — start with Bluesky, easily extend to other APIs.
- ⏳ Smart Pagination & Rate Limiting — respects API constraints.
- 🧹 Deduplication & Incremental Saving — prevents data loss on long runs.
- 📦 Unified Schema — standard structure for merging data from multiple sources.
- 🧱 Modular Design — import, modify, or deploy components independently.
- ⚙️ FastAPI Powered — deploy as a microservice or standalone backend.
