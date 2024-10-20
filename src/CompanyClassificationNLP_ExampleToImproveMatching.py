import praw
import spacy
# import json
import csv
from fuzzywuzzy import fuzz
import numpy as np
import h5py
h5py.run_tests()
print("NumPy version:", np.__version__)
print("h5py version:", h5py.__version__)

class RedditScraper:
    def __init__(self, client_id, client_secret, user_agent, ticker_list_file):
        # Initialize PRAW (Python Reddit API Wrapper)
        self.reddit = praw.Reddit(client_id=client_id,
                                  client_secret=client_secret,
                                  user_agent=user_agent)
        # Load ticker list from file
        with open(ticker_list_file, 'r') as file:
            self.ticker_list = json.load(file)
        # Load spaCy model for Named Entity Recognition
        self.nlp = spacy.load("en_core_web_sm")

    def match_companies_ner(self, comment_text):
        """
        Use Named Entity Recognition to identify companies in the given comment text.
        """
        doc = self.nlp(comment_text)
        companies = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
        return companies

    def match_companies(self, comment_text):
        corporate_identifiers = [
            "inc", "inc.", "corp", "corp.", "corporation", "company", "co", "co.", "s.a.", "group", "plc", "ltd", "ltd.", "limited", "ag", "nv", "holdings", "lp", "lp.", "sa", "sp.a", "se", "trust", "srl", "s.r.l.", "llc", "llc.", "etf", "reit", "partners", "capital", "industries", "international", "services", "spc", "gmbh", "bhd", "pte", "pte.", "sas", "societe", "limited.", "llp", "llp.", "s.a.b.", "kabushiki kaisha", "s.p.a.", "aktiengesellschaft", "oyj", "s.a.s.", "unlimited", "s.c.a.", "pte ltd", "public limited company", "s.a.p.i. de c.v.", ",", "."
        ]
        sec_dict = self.ticker_list
        relevant_tickers = []
        comment_words = [x.lower() for x in comment_text.split(" ")]

        with open('fuzzymatchlog.csv', 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ["Ticker", "Company Name", "Match Type", "Comment Words", "Company Words", "Comment", "Similarity Score"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for ticker, company_name in sec_dict.items():
                company_words = [x.lower() for x in company_name.split(" ")]
                # Remove common corporate structure words
                while company_words and company_words[-1].lower() in corporate_identifiers:
                    company_words = company_words[:-1]

                # Check for exact match
                if all(word in comment_words for word in company_words):
                    relevant_tickers.append(ticker)
                    print(f"Found exact reference to {ticker} ({company_name}) in the comment: {comment_text}.")
                    writer.writerow({
                        "Ticker": ticker,
                        "Company Name": company_name,
                        "Match Type": "Exact Match",
                        "Comment Words": " ".join(comment_words),
                        "Company Words": " ".join(company_words),
                        "Comment": comment_text,
                        "Similarity Score": "N/A"
                    })
                else:
                    # Fuzzy matching
                    similarity_score = fuzz.token_set_ratio(company_name, comment_text)
                    if similarity_score > 65:
                        relevant_tickers.append(ticker)
                        print(f"Found fuzzy reference to {ticker} ({company_name}) in the comment: {comment_text}.")
                        writer.writerow({
                            "Ticker": ticker,
                            "Company Name": company_name,
                            "Match Type": "Fuzzy Match",
                            "Comment Words": " ".join(comment_words),
                            "Company Words": " ".join(company_words),
                            "Comment": comment_text,
                            "Similarity Score": similarity_score
                        })

        return relevant_tickers

    def classify_companies(self, comments):
        """
        Classify companies based on scraped data using Named Entity Recognition and other matching methods.
        """
        classified_companies = []
        for comment in comments:
            ner_companies = self.match_companies_ner(comment["text"])
            ticker_matches = self.match_companies(comment["text"])
            classified_companies.append({
                "comment_id": comment["id"],
                "ner_companies": ner_companies,
                "ticker_matches": ticker_matches
            })
        return classified_companies

    def scrape_subreddit(self, subreddit_name, limit=100):
        """
        Scrape comments from a given subreddit.
        """
        subreddit = self.reddit.subreddit(subreddit_name)
        comments = []
        for submission in subreddit.hot(limit=limit):
            submission.comments.replace_more(limit=None)
            for comment in submission.comments.list():
                comments.append({
                    "id": comment.id,
                    "text": comment.body
                })
        return comments

# Initialize RedditScraper with Reddit credentials and ticker list file
client_id = "your_client_id"
client_secret = "your_client_secret"
user_agent = "your_user_agent"
ticker_list_file = "ticker_list.json"
scraper = RedditScraper(client_id, client_secret, user_agent, ticker_list_file)

# Sample usage: Scrape subreddit and classify companies
subreddit_name = "investing"
comments = scraper.scrape_subreddit(subreddit_name)
classified_data = scraper.classify_companies(comments)

# Save classified data to a file
with open('classified_companies.json', 'w', encoding='utf-8') as file:
    json.dump(classified_data, file, indent=4)

print("Company classification complete. Results saved to classified_companies.json.")