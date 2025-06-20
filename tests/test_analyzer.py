import pytest
import os
from src.RedditNLPAnalyzer import RedditScraper

# This fixture can be expanded to provide a more sophisticated scraper instance
# For now, it initializes the scraper for testing.
# Note: This requires environment variables for Reddit API to be set.
@pytest.fixture
def scraper_instance():
    """Provides a RedditScraper instance for testing."""
    client_id = os.environ.get('REDDIT_CLIENT_ID')
    client_secret = os.environ.get('REDDIT_CLIENT_SECRET')
    user_agent = os.environ.get('REDDIT_USER_AGENT')
    
    # Basic check to ensure credentials are set, otherwise skip tests that need them
    if not all([client_id, client_secret, user_agent]):
        pytest.skip("Reddit API credentials not found in environment variables.")
        
    return RedditScraper(client_id, client_secret, user_agent)

def test_company_recognition_with_ner(scraper_instance):
    """
    Tests that the Hugging Face NER model correctly identifies organizations.
    """
    text = "Apple announced a new partnership with Microsoft, while Google remained silent."
    expected_companies = ["Apple", "Microsoft", "Google"]
    
    # Run the NER function
    recognized_companies = scraper_instance.match_companies_ner_hf(text)
    
    # Assert that the recognized list contains all expected companies
    # Using a set for comparison makes it order-independent
    assert set(recognized_companies) == set(expected_companies)

def test_company_recognition_no_orgs(scraper_instance):
    """
    Tests that the NER model returns an empty list when no organizations are present.
    """
    text = "The weather is sunny and warm today."
    
    recognized_companies = scraper_instance.match_companies_ner_hf(text)
    
    assert recognized_companies == []

def test_company_recognition_with_noisy_text(scraper_instance):
    """
    Tests company recognition in text with mixed entities.
    """
    text = "John Doe from IBM traveled to Paris last week."
    expected_companies = ["IBM"]
    
    recognized_companies = scraper_instance.match_companies_ner_hf(text)
    
    assert set(recognized_companies) == set(expected_companies)

# To run these tests, execute `pytest` in the project root directory. 