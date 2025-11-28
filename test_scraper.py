#!/usr/bin/env python3
"""
Test script for Bluesky scraper with incremental saving.
Tests with a single keyword to verify functionality.
"""

import os
from dotenv import load_dotenv
from app.scrapers.scraper_bluesky import scrape_bluesky
from app.cache.cache_manager import load_from_cache
from app.utils.logger import get_logger

# Load environment
load_dotenv()
logger = get_logger()

def test_scraper():
    """Test the scraper with a single keyword."""

    test_keyword = "FATF"
    max_posts = 100
    cache_type = "csv"

    logger.info("="*80)
    logger.info("🧪 TESTING BLUESKY SCRAPER")
    logger.info("="*80)
    logger.info(f"Test keyword: {test_keyword}")
    logger.info(f"Max posts: {max_posts}")
    logger.info(f"Cache type: {cache_type}")
    logger.info(f"Incremental save: ENABLED (every 50 posts)")
    logger.info("")

    try:
        # Test scraping with incremental save
        logger.info("📥 Starting scrape with incremental saving...")
        df = scrape_bluesky(
            keyword=test_keyword,
            max_posts=max_posts,
            pause=2.0,
            enable_incremental_save=True,
            cache_type=cache_type,
            save_interval=50
        )

        logger.info("")
        logger.info("="*80)
        logger.info("✅ SCRAPE COMPLETED")
        logger.info("="*80)

        if df is not None and not df.empty:
            logger.info(f"Posts scraped: {len(df)}")
            logger.info(f"Columns: {list(df.columns)}")

            # Check location detection
            if 'country' in df.columns:
                country_counts = df['country'].value_counts()
                logger.info(f"\n📍 Location Detection Results:")
                for country, count in country_counts.items():
                    logger.info(f"   {country}: {count} posts")

            # Check cache
            logger.info(f"\n💾 Testing cache retrieval...")
            cached_df = load_from_cache(test_keyword, cache_type, "bluesky")
            if cached_df is not None:
                logger.info(f"✅ Cache working! Loaded {len(cached_df)} posts from cache")
            else:
                logger.warning(f"⚠️  Cache file not found or empty")

            # Show sample data
            logger.info(f"\n📄 Sample posts:")
            for idx, row in df.head(3).iterrows():
                logger.info(f"\n   Post {idx + 1}:")
                logger.info(f"   Author: {row.get('author', 'N/A')}")
                logger.info(f"   Text: {row.get('text', 'N/A')[:100]}...")
                logger.info(f"   Country: {row.get('country', 'N/A')}")
                logger.info(f"   Region: {row.get('region', 'N/A')}")
                logger.info(f"   Confidence: {row.get('confidence', 'N/A')}")
        else:
            logger.warning("⚠️  No posts found for this keyword")

        logger.info("\n" + "="*80)
        logger.info("🎉 TEST COMPLETED SUCCESSFULLY")
        logger.info("="*80)

    except Exception as e:
        logger.error(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_scraper()
