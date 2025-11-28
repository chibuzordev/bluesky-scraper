#!/usr/bin/env python3
"""
Bluesky CTF Dataset Scraper
Comprehensive scraper for Counter-Terrorism Financing research posts on Bluesky.

Features:
- Incremental saving: saves data after every batch (no data loss on crashes)
- Checkpointing: tracks completed keywords and can resume from interruptions
- Location detection: identifies UK/Nigeria regions from post content
- Deduplication: removes duplicate posts by URI
- Rate limiting: respects API limits with configurable delays
"""

import os
import sys
from dotenv import load_dotenv
from app.scrapers.scraper_bluesky import scrape_bluesky
from app.cache.cache_manager import (
    save_checkpoint,
    load_checkpoint,
    merge_all_caches
)
from app.utils.logger import get_logger
import time

# Load environment
load_dotenv()
logger = get_logger()

# ---------- KEYWORD LISTS ----------

CTF_CORE = [
    "Counter-terrorism",
    "Counter-terrorism financing",
    "Counter-terrorism policies on NGOs",
    "Impact of terrorism laws on charities",
    "Financial compliance Islamic charities",
    "Charity financial monitoring",
    "Effects of financial restrictions on NGOs",
    "Restricted funding",
    "Disrupted aid delivery",
    "Donor distrust",
    "Operational constraints",
    "FATF",
    "Financial Action Task Force",
    "Charity Commission",
    "Charity Commission UK",
    "OFSI",
    "HM Treasury",
    "NFIU",
    "EFCC",
    "EFCC Nigeria"
]

MUSLIM_CHARITIES = [
    # UK
    "Muslim Charities Forum",
    "Al-Mizan Charitable Trust",
    "Islamic Relief Worldwide",
    "Al-Khair Foundation",
    "Muslim Hands",
    "Human Appeal",
    "Islamic Help",
    "Muslim Aid",
    "One Nation",
    "One Nation UK",
    "Muslim Youth Helpline",
    "European Muslim Directory UK",

    # Nigeria
    "Islamic Charity Society of Nigeria",
    "Al Amin Islamic Foundation",
    "Islamic Education Trust",
    "Ummah Islamic Organisation",
    "Islamic Aid & Relief Foundation of Nigeria",
    "Islamic Provision",
    "Islamic Ummah Relief",
    "Muslim Aid Nigeria",
    "Oasis Muslim Care Foundation",
    "Al-Habibiyyah Islamic Society",
    "Jama'atu Nasril Islam",
    "National Hajj Commission of Nigeria",
    "Islamic Movement of Nigeria",
    "Nigerian Supreme Council for Islamic Affairs",
    "Federation of Muslim Women's Associations in Nigeria",
    "Abibakr As-Sidiq Philanthropic Home",
    "Muslim Public Affairs Centre"
]

COUNTRY_SPECIFIC = [
    "UK Muslim charities counter-terrorism",
    "UK counter-terrorism Muslim NGOs",
    "Muslim charities under investigation UK",
    "Zakat restrictions UK",
    "UK financial monitoring charities",
    "Nigeria counter-terrorism Muslim impact",
    "Financial regulations Muslim charities Nigeria",
    "Counter-terrorism effects on Nigerian NGOs",
    "Zakat and Sadaqah Nigeria compliance",
    "Nigerian NGOs under financial scrutiny",
    "Nigeria Muslim NGOs financial impact"
]

ANALYTICAL_THEMES = [
    "Ethnicity and CTF",
    "International Delegation and CTF",
    "President's Body Language in CTF",
    "Co-option of Good Muslim Charities",
    "Sectarianisation",
    "Fundamental British Values and CTF",
    "SWIFT and US Influence on CTF",
    "Constitutionalism and CTF",
    "Tokenism and Participatory Inequality",
    "Counter-discursive Reframing",
    "Resistance Pedagogy",
    "Politics of Professionalism and Rebranding",
    "Lobbying and Transnational Advocacy",
    "Political Socialisation",
    "Politics of Professionalisation"
]

HASHTAGS = [
    "#CounterTerrorism",
    "#MuslimCharities",
    "#NGOsUnderScrutiny",
    "#ZakatMonitoring",
    "#CharityCompliance",
    "#IslamicNGOs",
    "#CharityWatchdog",
    "#MuslimCommunityImpact",
    "#FinancialRegulations",
    "#DeRiskingNGOs"
]

# Combine all keywords
ALL_KEYWORDS = (
    CTF_CORE
    + MUSLIM_CHARITIES
    + COUNTRY_SPECIFIC
    + ANALYTICAL_THEMES
    + HASHTAGS
)

# ---------- CONFIGURATION ----------

SESSION_NAME = os.getenv("SCRAPE_SESSION_NAME", "ctf_dataset")
MAX_POSTS_PER_KEYWORD = int(os.getenv("MAX_POSTS_PER_KEYWORD", 5000))
PAUSE_BETWEEN_KEYWORDS = int(os.getenv("PAUSE_BETWEEN_KEYWORDS", 5))
PAUSE_BETWEEN_REQUESTS = float(os.getenv("PAUSE_BETWEEN_REQUESTS", 2.0))
OUTPUT_FILE = os.getenv("BLUESKY_OUTPUT_FILE", "bluesky_ctf_dataset.csv")
CACHE_TYPE = os.getenv("CACHE_TYPE", "csv")  # csv, sqlite, or json
SAVE_INTERVAL = int(os.getenv("SAVE_INTERVAL", 50))  # Save every N posts

def scrape_all_keywords_with_checkpointing():
    """
    Scrape all keywords with checkpointing and incremental saving.
    Can be stopped and resumed without losing progress.
    """
    logger.info(f"🚀 Starting CTF Dataset Scraper")
    logger.info(f"📋 Total keywords to process: {len(ALL_KEYWORDS)}")
    logger.info(f"📁 Output file: {OUTPUT_FILE}")
    logger.info(f"💾 Cache type: {CACHE_TYPE}")
    logger.info(f"🔄 Save interval: every {SAVE_INTERVAL} posts")
    logger.info(f"⏱️  Max posts per keyword: {MAX_POSTS_PER_KEYWORD}")

    # Load checkpoint if exists
    checkpoint = load_checkpoint(SESSION_NAME, platform="bluesky")
    completed_keywords = checkpoint.get('completed_keywords', []) if checkpoint else []

    if completed_keywords:
        logger.info(f"📌 Resuming from checkpoint: {len(completed_keywords)} keywords already completed")
    else:
        logger.info(f"📌 Starting fresh scrape session")

    # Filter out already completed keywords
    remaining_keywords = [kw for kw in ALL_KEYWORDS if kw not in completed_keywords]
    logger.info(f"🎯 Remaining keywords to process: {len(remaining_keywords)}")

    # Track stats
    total_posts_scraped = 0
    failed_keywords = []

    try:
        for idx, keyword in enumerate(remaining_keywords, start=1):
            logger.info(f"\n{'='*80}")
            logger.info(f"🔎 [{idx}/{len(remaining_keywords)}] Scraping keyword: '{keyword}'")
            logger.info(f"{'='*80}")

            try:
                # Scrape with incremental saving enabled
                df = scrape_bluesky(
                    keyword=keyword,
                    max_posts=MAX_POSTS_PER_KEYWORD,
                    pause=PAUSE_BETWEEN_REQUESTS,
                    enable_incremental_save=True,
                    cache_type=CACHE_TYPE,
                    save_interval=SAVE_INTERVAL
                )

                posts_count = len(df) if df is not None else 0
                total_posts_scraped += posts_count
                logger.info(f"✅ Completed '{keyword}': {posts_count} posts")

                # Mark keyword as completed
                completed_keywords.append(keyword)

                # Save checkpoint after each keyword
                save_checkpoint(
                    session_name=SESSION_NAME,
                    completed_keywords=completed_keywords,
                    platform="bluesky",
                    metadata={
                        "total_keywords": len(ALL_KEYWORDS),
                        "remaining_keywords": len(ALL_KEYWORDS) - len(completed_keywords),
                        "total_posts_scraped": total_posts_scraped,
                        "failed_keywords": failed_keywords
                    }
                )

                # Pause between keywords to respect rate limits
                if idx < len(remaining_keywords):
                    logger.info(f"⏸️  Pausing {PAUSE_BETWEEN_KEYWORDS}s before next keyword...")
                    time.sleep(PAUSE_BETWEEN_KEYWORDS)

            except Exception as e:
                logger.error(f"❌ Failed to scrape '{keyword}': {e}")
                failed_keywords.append(keyword)
                # Continue to next keyword instead of stopping
                continue

        # All keywords processed - merge results
        logger.info(f"\n{'='*80}")
        logger.info(f"🎉 Scraping completed!")
        logger.info(f"{'='*80}")
        logger.info(f"✅ Successfully scraped: {len(completed_keywords)} keywords")
        logger.info(f"❌ Failed keywords: {len(failed_keywords)}")
        if failed_keywords:
            logger.info(f"   Failed: {', '.join(failed_keywords)}")

        # Merge all caches into final output file
        logger.info(f"\n📊 Merging all cached data into final dataset...")
        final_df = merge_all_caches(
            keywords=completed_keywords,
            output_file=OUTPUT_FILE,
            cache_type=CACHE_TYPE,
            platform="bluesky"
        )

        if final_df is not None:
            logger.info(f"✅ Final dataset saved to: {OUTPUT_FILE}")
            logger.info(f"📈 Total unique posts: {len(final_df)}")

            # Print summary stats
            if 'country' in final_df.columns:
                logger.info(f"\n📍 Location Distribution:")
                country_counts = final_df['country'].value_counts()
                for country, count in country_counts.items():
                    logger.info(f"   {country}: {count} posts")
        else:
            logger.warning(f"⚠️  No data to merge")

    except KeyboardInterrupt:
        logger.info(f"\n\n⚠️  Scraping interrupted by user")
        logger.info(f"📌 Progress saved! You can resume later by running this script again.")
        logger.info(f"✅ Completed so far: {len(completed_keywords)}/{len(ALL_KEYWORDS)} keywords")
        sys.exit(0)

    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        logger.info(f"📌 Progress saved in checkpoint. You can resume later.")
        sys.exit(1)


if __name__ == "__main__":
    scrape_all_keywords_with_checkpointing()
