# Batch Scraping Guide

## Overview

The batch scraping endpoint allows you to scrape multiple keywords in a single API call. It features:

✅ **Checkpointing** - Resume from where you left off if interrupted
✅ **Incremental saving** - Each keyword is saved as it completes
✅ **Auto-merge** - Optionally merge all results into one dataset
✅ **Progress tracking** - See which keywords succeeded/failed

---

## API Endpoint

**POST** `/scrape/batch`

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `platform` | string | bluesky | Platform to scrape (bluesky, reddit, twitter, facebook, news) |
| `limit` | integer | 50 | Posts to fetch per keyword (10-5000) |
| `cache` | string | csv | Cache format (csv, json, sqlite) |
| `pause_between_keywords` | integer | 2 | Seconds to wait between keywords (0-60) |
| `merge_results` | boolean | false | Merge all results into single dataset |
| `session_name` | string | batch_scrape | Session name for checkpointing |

### Request Body

JSON array of keywords:

```json
{
  "keywords": [
    "Counter-terrorism",
    "FATF",
    "Islamic Relief Worldwide"
  ]
}
```

---

## Usage Examples

### Example 1: Basic Batch Scrape

Scrape 3 keywords from Bluesky:

```bash
curl -X POST "http://localhost:8000/scrape/batch?platform=bluesky&limit=100&cache=csv" \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": [
      "Counter-terrorism",
      "FATF",
      "Charity Commission"
    ]
  }'
```

**Response:**
```json
{
  "session_name": "batch_scrape",
  "platform": "bluesky",
  "total_keywords": 3,
  "already_completed": 0,
  "newly_scraped": 3,
  "failed": 0,
  "total_posts": 247,
  "results_per_keyword": [
    {"keyword": "Counter-terrorism", "posts": 89, "status": "success"},
    {"keyword": "FATF", "posts": 67, "status": "success"},
    {"keyword": "Charity Commission", "posts": 91, "status": "success"}
  ],
  "failed_keywords": [],
  "cache_type": "csv"
}
```

---

### Example 2: Batch with Merge

Scrape and merge into single dataset:

```bash
curl -X POST "http://localhost:8000/scrape/batch?platform=bluesky&limit=500&merge_results=true&session_name=ctf_research" \
  -H "Content-Type: application/json" \
  -d @keywords_for_api.json
```

**Response:**
```json
{
  "session_name": "ctf_research",
  "platform": "bluesky",
  "total_keywords": 92,
  "newly_scraped": 92,
  "failed": 0,
  "total_posts": 8542,
  "merged_file": "bluesky_ctf_research_merged.csv",
  "merged_posts": 8234,
  "download_url": "/scrape/export?platform=bluesky&format=csv",
  "cache_type": "csv"
}
```

---

### Example 3: Resume After Interruption

If the batch scrape is interrupted, simply run it again with the **same session_name**:

```bash
curl -X POST "http://localhost:8000/scrape/batch?platform=bluesky&session_name=ctf_research" \
  -H "Content-Type: application/json" \
  -d @keywords_for_api.json
```

It will automatically skip already-completed keywords:

```json
{
  "session_name": "ctf_research",
  "platform": "bluesky",
  "total_keywords": 92,
  "already_completed": 45,  // ← Skipped these
  "newly_scraped": 47,      // ← Only scraped remaining
  "total_posts": 4321
}
```

---

## Using the Swagger UI

### Step 1: Navigate to API Docs

Open your browser and go to:
```
http://localhost:8000/docs
```

### Step 2: Find the Batch Endpoint

Scroll to `POST /scrape/batch` under the **Scraping** section.

### Step 3: Click "Try it out"

### Step 4: Set Parameters

- **platform**: `bluesky`
- **limit**: `500`
- **cache**: `csv`
- **merge_results**: `true`
- **session_name**: `my_ctf_dataset`

### Step 5: Paste Keywords

In the **Request body** field, paste the contents of `keywords_for_api.json`:

```json
[
  "De-risking for counter-terrorism",
  "De-risking Muslim organizations",
  "Risk-based approach to counter-terrorism",
  "AML/CFT",
  ...
]
```

Or copy-paste directly from the file:

```bash
cat keywords_for_api.json
```

### Step 6: Execute

Click **Execute** and watch the progress in the response.

---

## Complete CTF Dataset Example

### Using Provided Keywords File

The repository includes `keywords_for_api.json` with **92 CTF-related keywords**:

- 25 CTF Core terms
- 29 Muslim Charities
- 11 Country-Specific
- 15 Analytical Themes
- 10 Hashtags

**To scrape all 92 keywords:**

```bash
curl -X POST "http://localhost:8000/scrape/batch?platform=bluesky&limit=5000&cache=csv&merge_results=true&session_name=ctf_full_dataset&pause_between_keywords=3" \
  -H "Content-Type: application/json" \
  -d @keywords_for_api.json
```

This will:
1. Scrape up to 5,000 posts per keyword
2. Save each keyword to cache individually
3. Wait 3 seconds between keywords (rate limiting)
4. Merge all results into `bluesky_ctf_full_dataset_merged.csv`
5. Create checkpoint for resuming if needed

**Estimated time:** ~4-6 hours (92 keywords × 3s pause + scraping time)

---

## Downloading Results

### Option 1: Download Individual Keyword

```bash
curl "http://localhost:8000/scrape/export?platform=bluesky&keyword=FATF&format=csv" -o fatf.csv
```

### Option 2: Download Merged Dataset

```bash
curl "http://localhost:8000/scrape/export?platform=bluesky&format=csv" -o ctf_dataset.csv
```

### Option 3: List All Available Files

```bash
curl "http://localhost:8000/scrape/export/list?platform=bluesky"
```

Response:
```json
{
  "total_files": 92,
  "files": [
    {
      "filename": "bluesky_fatf.csv",
      "platform": "bluesky",
      "keyword": "fatf",
      "format": "csv",
      "size_kb": 142.5
    },
    ...
  ]
}
```

---

## Error Handling

### Failed Keywords

If some keywords fail, they're listed in the response:

```json
{
  "failed": 3,
  "failed_keywords": ["Unknown Keyword", "Bad Query"],
  "results_per_keyword": [
    {"keyword": "Unknown Keyword", "posts": 0, "status": "failed", "error": "No results found"}
  ]
}
```

You can retry just the failed keywords by creating a new request with only those keywords.

---

## Best Practices

### 1. Use Meaningful Session Names
```
✅ session_name=ctf_uk_research
❌ session_name=batch_scrape
```

### 2. Set Appropriate Pauses
```
✅ pause_between_keywords=3  // Respectful to API
❌ pause_between_keywords=0  // May get rate limited
```

### 3. Start Small, Then Scale
```
# Test with 5 keywords first
curl -X POST "http://localhost:8000/scrape/batch?limit=50" \
  -d '{"keywords": ["FATF", "Counter-terrorism", "Charity Commission"]}'

# Then run full batch
curl -X POST "http://localhost:8000/scrape/batch?limit=5000" \
  -d @keywords_for_api.json
```

### 4. Monitor Progress

Check the logs while running:
```bash
# If running with uvicorn
tail -f logs/app.log
```

---

## Comparison: Batch vs. Individual

| Feature | Individual (`/scrape/bluesky`) | Batch (`/scrape/batch`) |
|---------|-------------------------------|------------------------|
| Keywords per call | 1 | Multiple |
| Checkpointing | ❌ No | ✅ Yes |
| Auto-resume | ❌ No | ✅ Yes |
| Merge results | ❌ Manual | ✅ Automatic |
| Progress tracking | ❌ No | ✅ Per-keyword |
| Rate limiting | Manual | ✅ Built-in |

---

## Troubleshooting

### "Already completed" shows wrong count

**Solution:** Different session names create different checkpoints. Use consistent session names:
```bash
# First run
session_name=my_dataset

# Resume run - use SAME name
session_name=my_dataset
```

### Download link returns 404

**Solution:** The merged file is created in the root directory. Use:
```bash
ls -la *.csv
```

### Too slow / timeout

**Solution:** Reduce keywords per batch or increase timeout:
```bash
# Split into smaller batches
keywords_batch_1.json  # First 30 keywords
keywords_batch_2.json  # Next 30 keywords
keywords_batch_3.json  # Last 32 keywords
```

---

## Keywords File Format

The `keywords_for_api.json` file contains all 92 CTF keywords in proper JSON format:

```json
[
  "De-risking for counter-terrorism",
  "De-risking Muslim organizations",
  "AML/CFT",
  ...
  "#DeRiskingNGOs"
]
```

You can edit this file to:
- Add more keywords
- Remove unwanted keywords
- Create custom keyword lists

Just maintain the JSON array format with commas between items.

---

## Summary

✅ **Easy batch scraping** - Upload keywords, get results
✅ **Safe & resumable** - Checkpointing prevents data loss
✅ **Flexible** - Scrape, cache, merge all in one call
✅ **Production-ready** - Built-in rate limiting and error handling

For the complete CTF dataset (92 keywords), simply paste `keywords_for_api.json` into the Swagger UI or use the curl command above!
