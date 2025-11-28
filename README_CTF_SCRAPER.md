# Bluesky CTF Dataset Scraper

A robust scraper for collecting Counter-Terrorism Financing (CTF) research data from Bluesky with proper caching, checkpointing, and location detection.

## 🎯 Key Features

### 1. **Incremental Saving** ✅
- Saves data every 50 posts (configurable via `SAVE_INTERVAL`)
- No data loss if script crashes or is interrupted
- Data is immediately written to cache files

### 2. **Checkpointing** ✅
- Tracks which keywords have been completed
- Can resume from where it left off after interruptions
- Checkpoint files stored in `app/cache/checkpoints/`

### 3. **Location Detection** ✅
- Automatically detects UK and Nigeria regions from:
  - Post text content
  - User bio
  - Display name
  - Handle
- Three confidence levels: High, Medium, Low
- Identifies 40+ UK regions and 37+ Nigerian states

### 4. **Deduplication** ✅
- Removes duplicate posts by URI
- Works both within single keyword scrapes and across merged datasets

### 5. **Rate Limiting** ✅
- Configurable delays between requests (default: 2 seconds)
- Configurable delays between keywords (default: 5 seconds)
- Prevents API throttling

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Configuration

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Edit `.env` with your Bluesky credentials:
```env
BLUESKY_USERNAME=your_username.bsky.social
BLUESKY_APP_PASSWORD=your-app-password
```

### Running the Scraper

```bash
python scrape_ctf_dataset.py
```

## 📋 Configuration Options

Edit `.env` to customize:

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_POSTS_PER_KEYWORD` | 5000 | Maximum posts to fetch per keyword |
| `PAUSE_BETWEEN_KEYWORDS` | 5 | Seconds to wait between keywords |
| `PAUSE_BETWEEN_REQUESTS` | 2.0 | Seconds to wait between API requests |
| `SAVE_INTERVAL` | 50 | Save to cache every N posts |
| `CACHE_TYPE` | csv | Cache format (csv, sqlite, json) |
| `OUTPUT_FILE` | bluesky_ctf_dataset.csv | Final merged output file |

## 🔄 Resume After Interruption

If the script is interrupted (Ctrl+C, crash, etc.):

1. Simply run it again: `python scrape_ctf_dataset.py`
2. It will automatically load the checkpoint
3. It will skip already-completed keywords
4. It will continue from where it left off

## 📊 Keywords Covered

The scraper searches for **100+ keywords** across:

- **CTF Core** (20 keywords): Counter-terrorism, FATF, Charity Commission, etc.
- **Muslim Charities** (29 keywords): Islamic Relief, Al-Khair Foundation, Muslim Aid Nigeria, etc.
- **Country-Specific** (11 keywords): UK/Nigeria-specific CTF topics
- **Analytical Themes** (15 keywords): Academic research themes
- **Hashtags** (10 keywords): Social media hashtags

## 📁 Output Structure

### Cache Files
- Location: `app/cache/cached_files/`
- Format: `bluesky_{keyword}.csv` (or .sqlite/.json)
- One file per keyword

### Checkpoints
- Location: `app/cache/checkpoints/`
- Format: `bluesky_ctf_dataset_checkpoint.json`
- Tracks progress and metadata

### Final Dataset
- Location: Root directory
- Filename: `bluesky_ctf_dataset.csv`
- Merged and deduplicated results from all keywords

## 📄 Data Schema

Each row contains:

| Column | Description |
|--------|-------------|
| `keyword` | Search keyword used |
| `uri` | Unique post identifier |
| `author` | Post author handle |
| `display_name` | Author's display name |
| `did` | Decentralized identifier |
| `text` | Post content |
| `created_at` | Timestamp |
| `bio` | Author bio |
| `country` | Detected country (UK/Nigeria/None) |
| `region` | Detected region (e.g., "Lagos", "Greater London") |
| `confidence` | Detection confidence (High/Medium/Low) |

## 🛠️ Improvements Over Original Code

### Before (Colab Version)
- ❌ Lost all progress on crashes
- ❌ Saved only at the very end
- ❌ No resume capability
- ❌ All data kept in memory
- ❌ Hardcoded credentials

### After (This Version)
- ✅ Incremental saving (every 50 posts)
- ✅ Checkpoint/resume capability
- ✅ Memory efficient (saves batches)
- ✅ Environment-based config
- ✅ Better error handling
- ✅ Detailed logging
- ✅ Progress tracking

## 📈 Example Output

```
🚀 Starting CTF Dataset Scraper
📋 Total keywords to process: 100
📁 Output file: bluesky_ctf_dataset.csv
💾 Cache type: csv
🔄 Save interval: every 50 posts

================================================================================
🔎 [1/100] Scraping keyword: 'Counter-terrorism'
================================================================================
✅ Incrementally saved 50 posts to cache
✅ Incrementally saved 100 posts to cache
✅ Completed 'Counter-terrorism': 127 posts
⏸️  Pausing 5s before next keyword...

[... continues ...]

🎉 Scraping completed!
✅ Successfully scraped: 100 keywords
📊 Merging all cached data into final dataset...
✅ Final dataset saved to: bluesky_ctf_dataset.csv
📈 Total unique posts: 8,542

📍 Location Distribution:
   UK: 3,241 posts
   Nigeria: 2,876 posts
   None: 2,425 posts
```

## 🔧 Troubleshooting

### Authentication Error
```
Error: Bluesky authentication failed
```
**Solution**: Check your credentials in `.env`

### Rate Limit Error
```
Error during pagination: Rate limit exceeded
```
**Solution**: Increase `PAUSE_BETWEEN_REQUESTS` in `.env`

### No Data Found
```
No posts found for '{keyword}'
```
**Solution**: Normal - some keywords may have no results

## 📝 Notes

- The scraper is designed for research purposes
- Respects Bluesky's API rate limits
- Uses exponential backoff for errors
- Location detection is heuristic-based
- Checkpoint files are JSON format
- Safe to interrupt with Ctrl+C

## 🤝 Support

For issues or questions, check the logs in the console output or review cached files in `app/cache/`.
