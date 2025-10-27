from scraper_bluesky import scrape_bluesky
# from scraper_reddit import scrape_reddit   # (coming soon)

def get_scraper(platform: str):
    """
    Dynamically returns the scraper function for a given platform.
    """
    platform = platform.lower().strip()

    scrapers = {
        "bluesky": scrape_bluesky,
        # "reddit": scrape_reddit,  # Add others here later
    }

    return scrapers.get(platform)
