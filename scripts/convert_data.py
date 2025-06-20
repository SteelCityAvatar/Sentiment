import sys
import os
import json
import pandas as pd
import logging

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.config import config
from src.core import logging_config

def convert_json_to_parquet():
    logging_config.setup_logging()
    logger = logging.getLogger(__name__)

    try:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        raw_path = os.path.join(project_root, config['data']['raw'])
        processed_path = os.path.join(project_root, config['data']['processed'])
        
        logger.info(f"Reading raw JSON data from: {raw_path}")
        with open(raw_path) as f:
            data = json.load(f)

        rows = []
        for entry in data:
            date = pd.to_datetime(entry['date'], unit='s')
            text = entry['text']
            companies = entry.get('ner_companies_hf', [])
            scores = entry.get('Sentiment_score', [])
            if not scores or not companies:
                continue  # Skip if no sentiment or no companies
            scores = scores[0]
            if not scores:
                continue  # Skip if sentiment score list is empty
            top = max(scores, key=lambda x: x['score'])
            for company in companies:
                rows.append({
                    'date': date,
                    'company': company,
                    'sentiment_label': top['label'],
                    'sentiment_score': top['score'],
                    'text': text
                })

        df = pd.DataFrame(rows)
        df.to_parquet(processed_path)
        logger.info(f"Conversion complete! Parquet file saved to {processed_path}")
    except Exception as e:
        logger.error(f"Error during conversion: {e}")

if __name__ == "__main__":
    convert_json_to_parquet() 