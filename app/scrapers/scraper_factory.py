from app.scrapers.scraper_bluesky import scrape_bluesky
from app.scrapers.scraper_reddit import scrape_reddit
from app.scrapers.scraper_twitter import scrape_twitter
from app.scrapers.scraper_facebook import scrape_facebook
from app.scrapers.scraper_news import scrape_news

def get_scraper(platform: str):
    """
    Dynamically returns the scraper function for a given platform.
    """
    platform = platform.lower().strip()

    scrapers = {
        "bluesky": scrape_bluesky,
        "reddit": scrape_reddit,
        "twitter": scrape_twitter,
        "x": scrape_twitter,  # Alias for Twitter
        "facebook": scrape_facebook,
        "news": scrape_news,
    }

    return scrapers.get(platform)

