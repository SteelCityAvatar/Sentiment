import praw
import spacy
import json
import csv
from fuzzywuzzy import fuzz
import numpy as np
import h5py
import os
os.getcwd()
print("NumPy version:", np.__version__)
print("h5py version:", h5py.__version__)
# src\CompanyClassificationNLP_ExampleToImproveMatching.py
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
        self.nlp = spacy.load("en_core_web_md")

    def match_companies_ner(self, comment_text):
        """
        Use Named Entity Recognition to identify companies in the given comment text.
        """
        print(comment_text)
        doc = self.nlp(comment_text)
        companies = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
        return companies
    def match_companies(self, comment_text):
        corporate_identifiers = [
            "inc", "inc.", "corp", "corp.", "corporation", "company", "co", "co.", "s.a.", "group", "plc", "ltd", "ltd.", "limited", "ag", "nv", "holdings", "lp", "lp.", "sa", "sp.a", "se", "trust", "srl", "s.r.l.", "llc", "llc.", "etf", "reit", "partners", "capital", "industries", "international", "services", "spc", "gmbh", "bhd", "pte", "pte.", "sas", "societe", "limited.", "llp", "llp.", "s.a.b.", "kabushiki kaisha", "s.p.a.", "aktiengesellschaft", "oyj", "s.a.s.", "unlimited", "s.c.a.", "pte ltd", "public limited company", "s.a.p.i. de c.v.", ",", "."
        ]
        sec_dict = self.ticker_list
        relevant_tickers = []
        
        # Debugging print statements
        print(f"Type of comment_text: {type(comment_text)}")
        print(f"Value of comment_text: {comment_text}")

        if not isinstance(comment_text, str):
            raise ValueError("Expected comment_text to be a string")
        
        comment_words = comment_text.lower().split(" ")
        print(comment_words == [x.lower() for x in comment_text.split(" ")])
    #     comment_words = [x.lower() for x in comment_text.split(" ")]
    
        with open('fuzzymatchlog.csv', 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ["Ticker", "Company Name", "Match Type", "Comment Words", "Company Words", "Comment", "Similarity Score"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for ticker, company_name in sec_dict.items():
                print(type(company_name['title']))
                print(company_name['ticker'])
                print(company_name['title'])
                company_words = [x.lower() for x in company_name['title'].split(" ")]
                # Remove common corporate structure words
                while company_words and company_words[-1].lower() in corporate_identifiers:
                    company_words = company_words[:-1]

                # Check for exact match
                if all(word in comment_words for word in company_words):
                    relevant_tickers.append(company_name['ticker'])
                    print(f"Found exact reference to {company_name['ticker']} ({company_name['title']}) in the comment: {comment_text}.")
                    writer.writerow({
                        "Ticker": company_name['ticker'],
                        "Company Name": company_name['title'],
                        "Match Type": "Exact Match",
                        "Comment Words": " ".join(comment_words),
                        "Company Words": " ".join(company_words),
                        "Comment": comment_text,
                        "Similarity Score": "N/A"
                    })
                else:
                    # Fuzzy matching
                    similarity_score = fuzz.token_set_ratio(company_name['title'], comment_text)
                    if similarity_score > 85:
                        relevant_tickers.append(company_name['ticker'])
                        print(f"Found fuzzy reference to {company_name['ticker']} ({company_name['title']}) in the comment: {comment_text}.")
                        writer.writerow({
                            "Ticker": company_name['ticker'],
                            "Company Name": company_name['title'],
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
        i=0
        for comment in comments:
            print(i)
            print(comment['text'].split())

            ner_companies = self.match_companies_ner(comment["text"])
            ticker_matches = self.match_companies(comment["text"])
            classified_companies.append({
                "comment_id": comment["id"],
                "ner_companies": ner_companies,
                'comment_text': comment['text'],
                "ticker_matches": ticker_matches
            })
            print(i)
            i+=1
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
client_id = os.environ.get('REDDIT_CLIENT_ID')
client_secret = os.environ.get('REDDIT_CLIENT_SECRET')
user_agent = os.environ.get('REDDIT_USER_AGENT')
openai_api_key = os.environ.get('OPENAI_API_KEY')

ticker_list_file = r"C:\Users\anura\Documents\PyProjects\FoolAround\SentimentScraper_Project\SupportingFiles\company_tickers.json"

scraper = RedditScraper(client_id, client_secret, user_agent, ticker_list_file)

# Sample usage: Scrape subreddit and classify companies
subreddit_name = "ValueInvesting"
comments = scraper.scrape_subreddit(subreddit_name)

# for comment in comments:
#     print(comment["text"].split(" "))
#     scraper.match_companies(comment["text"])

classified_data = scraper.classify_companies(comments)
import pandas as pd
pd.json_normalize(classified_data).to_csv(r'C:\Users\anura\Documents\PyProjects\FoolAround\SentimentScraper_Project\SupportingFiles\classified_companies_vi.csv', index = False)
# Save classified data to a file
with open('classified_companies.json', 'w', encoding='utf-8') as file:
    json.dump(classified_data, file, indent=4)

print("Company classification complete. Results saved to classified_companies.json.")

