import sys
import os
import pandas as pd
import numpy as np
import json
import requests
import gc
import psutil
from datetime import datetime
from transformers import pipeline
from concurrent.futures import ThreadPoolExecutor, TimeoutError

# Add the path to the sys.path list
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Get project root directory
project_path = os.path.join(base_dir, 'src')  # Define project source path
support_files = os.path.join(base_dir, 'SupportingFiles')  # Define supporting files path
sys.path.append(project_path)  # Add project path to system path

# from RedditScraper import RedditFinancialScraper
from RedditNLPAnalyzer import RedditScraper

def log_system_usage():
    """
    Logs the current CPU and memory usage of the script.
    """
    process = psutil.Process(os.getpid())  # Get the current process
    print(f"CPU Usage: {psutil.cpu_percent()}%, Memory Usage: {process.memory_info().rss / (1024 ** 2):.2f} MB")

def reset_models(scraper):
    """
    Reload the models for the scraper to reset their state.
    """
    print("Reloading models to reset state...")
    scraper.hf_ner = pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03-english", grouped_entities=True)  # Reload Hugging Face model

def safe_execute(function, timeout, *args, **kwargs):
    """
    Executes a function with a timeout.
    """
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(function, *args, **kwargs)  # Submit function to executor
        try:
            return future.result(timeout=timeout)  # Attempt to get result within the timeout
        except TimeoutError:
            print(f"Timeout reached for {function.__name__}. Skipping...")
            return []

if __name__ == '__main__':
    try:
        
        import os
        client_id = os.environ.get('REDDIT_CLIENT_ID')  # Get Reddit client ID from environment
        client_secret = os.environ.get('REDDIT_CLIENT_SECRET')  # Get Reddit client secret from environment

        user_agent = os.environ.get('REDDIT_USER_AGENT')  # Get Reddit user agent from environment

        ticker_list_file = os.path.join(base_dir, 'SupportingFiles', 'company_tickers.json')  # Path to ticker list file
        scraper = RedditScraper(client_id, client_secret, user_agent, ticker_list_file)

        subreddit_name = "ValueInvesting" 
        comments = scraper.scrape_subreddit(subreddit_name, limit=1)
        # scraper.classify_companies(comments)#,timeout=100
        safe_execute(scraper.classify_companies, 100, comments)
    except Exception as e:
        print(f"Unhandled error: {e}")