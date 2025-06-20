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
import logging
from src.core import logging_config
from src.core.config import config
from src.processing.scraper import RedditScraper

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# from RedditScraper import RedditFinancialScraper

# --- System Monitoring Setup ---
# Attempt to import and initialize pynvml for GPU monitoring
try:
    import pynvml
    pynvml.nvmlInit()
    GPU_ENABLED = True
    logging.info("pynvml initialized successfully. GPU monitoring is enabled.")
except ImportError:
    GPU_ENABLED = False
    logging.info("pynvml not found. GPU monitoring is disabled.")
except pynvml.NVMLError as e:
    GPU_ENABLED = False
    logging.info(f"pynvml failed to initialize. GPU monitoring is disabled. Error: {e}")

# Setup logging
logging_config.setup_logging()

def log_system_usage():
    """Logs the current CPU, memory, and GPU usage."""
    process = psutil.Process(os.getpid())
    cpu_usage = f"CPU: {psutil.cpu_percent()}%"
    mem_usage = f"Mem: {process.memory_info().rss / (1024 ** 2):.2f}MB"
    
    gpu_usage_str = ""
    if GPU_ENABLED:
        try:
            # Get number of GPUs
            device_count = pynvml.nvmlDeviceGetCount()
            
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                name_raw = pynvml.nvmlDeviceGetName(handle)
                # Handle both string and bytes return types
                name = name_raw.decode('utf-8') if isinstance(name_raw, bytes) else name_raw
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                gpu_util = pynvml.nvmlDeviceGetUtilizationRates(handle).gpu
                gpu_mem_used = mem_info.used / (1024 ** 2)
                gpu_mem_total = mem_info.total / (1024 ** 2)
                gpu_usage_str += f" | GPU {i} ({name}): Util {gpu_util}%, Mem {gpu_mem_used:.2f}/{gpu_mem_total:.2f}MB"
        except pynvml.NVMLError as e:
            gpu_usage_str = f" | GPU status error: {e}"

    logging.info(f"System Usage - {cpu_usage} | {mem_usage}{gpu_usage_str}")

def reset_models(scraper):
    """
    Reload the models for the scraper to reset their state.
    """
    logging.info("Reloading models to reset state...")
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
            logging.warning(f"Timeout reached for {function.__name__}. Skipping...")
            return []

if __name__ == '__main__':
    try:
        logging.info("--- Starting Scraper Execution ---")
        client_id = os.environ.get('REDDIT_CLIENT_ID')
        client_secret = os.environ.get('REDDIT_CLIENT_SECRET')
        user_agent = os.environ.get('REDDIT_USER_AGENT')

        # Initialize the scraper without the hardcoded ticker file
        scraper = RedditScraper(client_id, client_secret, user_agent)

        # Get settings from the config file
        subreddit_name = config['subreddit_name']
        scrape_limit = config['scrape_limit']
        
        logging.info(f"Starting scrape for subreddit: {subreddit_name} with limit: {scrape_limit}")

        comments = scraper.scrape_subreddit(subreddit_name, limit=scrape_limit)
        
        safe_execute(scraper.classify_companies, 3600, comments) # Increased timeout
        logging.info("--- Scraper Execution Finished ---")
        
    except Exception as e:
        logging.error(f"Unhandled error in execute_scraper: {e}", exc_info=True)
    finally:
        # Ensure nvml is shutdown cleanly
        if GPU_ENABLED:
            pynvml.nvmlShutdown()
            logging.info("pynvml shutdown.")