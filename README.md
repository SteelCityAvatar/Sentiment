# Reddit Financial Sentiment Analyzer

This project scrapes Reddit posts and comments from a specified subreddit, identifies company mentions using Named Entity Recognition (NER), and analyzes the sentiment of each post/comment. The results are saved for further analysis, making it useful for financial research, sentiment tracking, and investment insights.

## Features

- **Reddit Scraping**: Collects posts and comments from a target subreddit using the Reddit API (PRAW).
- **Company Recognition**: Uses Hugging Face NER models to identify company names and tickers in text.
- **Sentiment Analysis**: Classifies sentiment (positive/negative) for each post/comment using Hugging Face pipelines.
- **Custom Ticker List**: Matches company mentions against a comprehensive ticker list.
- **Output**: Saves results (including company mentions and sentiment) to JSON and CSV files for further analysis.

## Folder Structure

```
Sentiment/
  ├── src/
  │   ├── execute_scraper.py         # Main script to run the pipeline
  │   └── RedditNLPAnalyzer.py       # Core logic for scraping, NER, and sentiment
  ├── SupportingFiles/
  │   └── company_tickers.json       # List of companies and tickers (JSON)
  ├── OutputFiles/
  │   └── comments_with_classification.json  # Output: comments with NER and sentiment
  └── ...
```

## Requirements

- Python 3.7+
- [PRAW](https://praw.readthedocs.io/) (Reddit API)
- [transformers](https://huggingface.co/transformers/) (Hugging Face pipelines)
- pandas
- numpy
- requests
- psutil
- fuzzywuzzy

You can install the dependencies with:

```bash
pip install praw transformers pandas numpy requests psutil fuzzywuzzy
```

## Setup

1. **Reddit API Credentials**:  
   Create a Reddit app at [https://www.reddit.com/prefs/apps](https://www.reddit.com/prefs/apps) and set the following environment variables:
   - `REDDIT_CLIENT_ID`
   - `REDDIT_CLIENT_SECRET`
   - `REDDIT_USER_AGENT`

2. **Company Ticker List**:  
   Ensure `SupportingFiles/company_tickers.json` exists. This file should be a JSON object mapping tickers to company names.

## Usage

Run the main script from the project root:

```bash
python src/execute_scraper.py
```

- By default, it scrapes the `ValueInvesting` subreddit (can be changed in the script).
- The script will:
  - Scrape posts and comments.
  - Identify company mentions using NER.
  - Analyze sentiment.
  - Save results to `OutputFiles/comments_with_classification.json`.

## Output

- **comments_with_classification.json**:  
  Each entry contains:
  - `id`: Reddit post/comment ID
  - `text`: The content
  - `type`: "post" or "comment"
  - `date`: UTC timestamp
  - `ner_companies_hf`: List of recognized companies
  - `Sentiment_score`: Sentiment label and score

Example:
```json
{
  "id": "m1d3p0h",
  "text": "Is anybody a Vital Farms investor? ...",
  "type": "comment",
  "date": 1733841495.0,
  "ner_companies_hf": ["Vital Farms", "CNBC", "DC"],
  "Sentiment_score": [{"label": "POSITIVE", "score": 0.96}]
}
```

## Customization

- **Subreddit**:  
  Change the `subreddit_name` variable in `execute_scraper.py` to target a different subreddit.
- **Scrape Limit**:  
  Adjust the `limit` parameter in `scrape_subreddit()` for more/less data.

## Notes

- The script uses Hugging Face models, which may download weights on first run.
- Intermediate results are saved every 10 comments to prevent data loss.
- The script is designed to be memory-efficient and can reset models if needed.

## Author

- Anurag Purker 