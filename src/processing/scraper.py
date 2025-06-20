"""
Authors: Anurag Purker

"""
import sys
import os
import praw
import json
import gc
from transformers import pipeline
import pandas as pd
from fuzzywuzzy import fuzz
import logging
from .config_loader import get_path

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.core.config import config

logger = logging.getLogger(__name__)

class RedditScraper:
    def __init__(self, client_id, client_secret, user_agent):
        # Initialize PRAW (Python Reddit API Wrapper)
        self.reddit = praw.Reddit(client_id=client_id,  # Reddit API client ID
                                  client_secret=client_secret,  # Reddit API client secret
                                  user_agent=user_agent)  # User agent for the API

        # Load ticker list from file
        ticker_list_file = get_path('supporting_files', 'company_tickers')
        with open(ticker_list_file, 'r') as file:
            self.ticker_list = json.load(file)

        # Load Hugging Face pipeline for NER
        self.hf_ner = pipeline("ner",
                                model=config['models']['ner'],
                                grouped_entities=True)

        # Initialize DistilRoBERTa fine-tuned for financial sentiment
        self.sentiment_pipeline = pipeline("sentiment-analysis",
                                        model=config['models']['sentiment'],
                                        return_all_scores=True)
        
        # Initialize current index for processing
        self.current_index = 0 
    
    def analyze_sentiment(self, text):
        """
        Analyze the sentiment of the given text using the Hugging Face sentiment pipeline.
        """
        try:
            # Use the sentiment pipeline to analyze the text
            sentiment = self.sentiment_pipeline(text)
            return sentiment
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}", exc_info=True)
            return []

    def match_companies_ner_hf(self, comment_text):
        """
        Use Hugging Face Named Entity Recognition to identify companies in the given comment text.
        """
        try:
            # Process the comment text with Hugging Face pipeline
            entities = self.hf_ner(comment_text)  
            # Extract entities labeled as organizations
            companies = [entity['word'] for entity in entities if entity['entity_group'] == 'ORG']
            return companies
        except Exception as e:
            logger.error(f"Hugging Face NER error: {e}", exc_info=True)
            return []
        
    def scrape_subreddit(self, subreddit_name, limit=100):
        """
        Scrape posts and comments from a given subreddit.
        """
        try:
            subreddit = self.reddit.subreddit(subreddit_name)  # Access subreddit by name
            data = []  # Initialize list to store posts and comments

            # Iterate through hot submissions in the subreddit
            for submission in subreddit.hot(limit=limit):
                # Add the submission (post) itself to the list
                data.append({
                    "id": submission.id,
                    "text": submission.selftext if submission.selftext else submission.title,
                    "type": "post",  # Indicate this is a post
                    "date": submission.created_utc  # Add submission date
                })

                # Expand and add all comments from the submission
                submission.comments.replace_more(limit=None)  # Expand all comments
                for comment in submission.comments.list():
                    data.append({
                        "id": comment.id,
                        "text": comment.body,
                        "type": "comment",  # Indicate this is a comment
                        "date": comment.created_utc  # Add comment date
                    })

            return data
        except Exception as e:
            logger.error(f"Reddit API error while scraping {subreddit_name}: {e}", exc_info=True)
            return []
  
    def _get_output_path(self, filename_key):
        """Constructs the full output path from the config."""
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        return os.path.join(project_root, config['data'][filename_key])

    def classify_companies(self, comments, threshold=85):
        """
        Classify companies based on scraped data using Named Entity Recognition and other matching methods.
        """
        classified_companies = []  # Initialize list to store classified companies

        # Iterate through comments starting from the current index
        while self.current_index < len(comments):
            i = self.current_index  # Get the current index
            try:
                logger.info(f"Processing comment {i + 1}/{len(comments)}: {comments[i]['id']}")

                # Process comment text with Hugging Face NER
                ner_companies_hf = self.match_companies_ner_hf(comments[i]["text"])
                logger.debug(f"Hugging Face NER results: {ner_companies_hf}")

                # Process comment text with Hugging Face sentiment analysis
                sentiment = self.analyze_sentiment(comments[i]["text"])
                logger.debug(f"Sentiment analysis results: {sentiment}")

                logger.info(comments[i]["text"])

                # Update the comment with NER and sentiment results
                comments[i]["ner_companies_hf"] = ner_companies_hf
                comments[i]["Sentiment_score"] = sentiment

                classified_companies.append({
                    "comment_id": comments[i]["id"],
                    "ner_companies_hf": ner_companies_hf,
                    "comment_text": comments[i]["text"],
                    'Sentiment_score': sentiment,
                    "date": comments[i]["date"]  # Include comment date
                })

                # Save intermediate results every 10 comments
                if (i + 1) % 10 == 0:
                    temp_output_path = f'temp_classified_companies_{i + 1}.csv'
                    pd.json_normalize(classified_companies).to_csv(temp_output_path, index=False)
                    logger.info(f"Intermediate results saved to {temp_output_path}.")

                # Force garbage collection to manage memory
                gc.collect()

                self.current_index += 1  # Move to the next comment

            except Exception as e:
                # Log errors for the current comment and move to the next
                logger.error(f"Unhandled error with comment {i + 1}/{len(comments)}: {e}", exc_info=True)
                self.current_index += 1

        # Final save of all classified data
        try:
            output_path = self._get_output_path('raw')
            # Ensure the directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(comments, f, indent=4)
            
            logger.info(f"Successfully classified and saved {len(comments)} comments to {output_path}")
        except Exception as e:
            logger.error(f"Error resolving classified data path: {e}", exc_info=True)

        return classified_companies

    def reset_models(self):
        """
        Reload models to reset state and manage potential issues.
        """
        logger.info("Reloading models to reset state...")
        self.hf_ner = pipeline("ner",  # Reload Hugging Face pipeline
                                model=config['models']['ner'],
                                grouped_entities=True)
        gc.collect()
