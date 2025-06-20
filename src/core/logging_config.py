import logging
import sys
from .config_loader import get_path

def setup_logging():
    """
    Configures the logging for the entire application.
    
    - Logs INFO and higher to the console.
    - Logs DEBUG and higher to a file specified in the config.
    """
    # Get log file path from config and ensure the directory exists
    log_file_path = get_path('log_file')
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Set the lowest level to capture all messages

    # Prevent duplicate handlers if this function is called multiple times
    if logger.hasHandlers():
        logger.handlers.clear()

    # --- Console Handler ---
    # Logs INFO and higher to the console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # --- File Handler ---
    # Logs DEBUG and higher to the log file
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    logging.info("Logging configured successfully.")

# You can call this once at the start of your main application script
# e.g., in execute_scraper.py 