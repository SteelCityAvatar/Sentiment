import praw
import spacy
import json
import gc
from transformers import pipeline
import pandas as pd
from fuzzywuzzy import fuzz

class RedditScraper:
    def __init__(self, client_id, client_secret, user_agent, ticker_list_file):
        # Initialize PRAW (Python Reddit API Wrapper)
        self.reddit = praw.Reddit(client_id=client_id,  # Reddit API client ID
                                  client_secret=client_secret,  # Reddit API client secret
                                  user_agent=user_agent)  # User agent for the API

        # Load ticker list from file
        with open(ticker_list_file, 'r') as file:
            self.ticker_list = json.load(file)  # Load JSON data from file

        # Load spaCy model for Named Entity Recognition (NER)
        # self.nlp = spacy.load("en_core_web_lg")  # Use medium-sized English model

        # Load Hugging Face pipeline for NER
        self.hf_ner = pipeline("ner",  # Use "ner" pipeline for Named Entity Recognition
                                model='dbmdz/bert-large-cased-finetuned-conll03-english',  # Pretrained BERT model
                                grouped_entities=True)  # Group consecutive entity tokens

        self.current_index = 0  # To track where we left off in processing comments

    # def match_companies_ner_spacy(self, comment_text):
    #     """
    #     Use spaCy Named Entity Recognition to identify companies in the given comment text.
    #     """
    #     try:
    #         doc = self.nlp(comment_text)  # Process the comment text with spaCy
    #         # Extract entities labeled as organizations or geopolitical entities
    #         companies = [ent.text for ent in doc.ents if ent.label_ in ["ORG", "GPE"]]
    #         return companies
    #     except Exception as e:
    #         print(f"spaCy error: {e}")  # Log errors if spaCy fails
    #         return []

    def match_companies_ner_hf(self, comment_text):
        """
        Use Hugging Face Named Entity Recognition to identify companies in the given comment text.
        """
        try:
            entities = self.hf_ner(comment_text)  # Process the comment text with Hugging Face pipeline
            # Extract entities labeled as organizations
            companies = [entity['word'] for entity in entities if entity['entity_group'] == 'ORG']
            return companies
        except Exception as e:
            print(f"Hugging Face error: {e}")  # Log errors if Hugging Face pipeline fails
            return []

    def scrape_subreddit(self, subreddit_name, limit=100):
        """
        Scrape comments from a given subreddit.
        """
        try:
            subreddit = self.reddit.subreddit(subreddit_name)  # Access subreddit by name
            comments = []  # Initialize list to store comments
            # Iterate through hot submissions in the subreddit
            for submission in subreddit.hot(limit=limit):
                submission.comments.replace_more(limit=None)  # Expand all comments
                for comment in submission.comments.list():
                    # Add comment ID and text to the list
                    comments.append({
                        "id": comment.id,
                        "text": comment.body
                    })
            return comments
        except Exception as e:
            print(f"Reddit API error: {e}")  # Log errors if Reddit API call fails
            return []

    def classify_companies(self, comments, reset_interval=50):
        """
        Classify companies based on scraped data using Named Entity Recognition and other matching methods.
        """
        classified_companies = []  # Initialize list to store classified companies

        # Iterate through comments starting from the current index
        while self.current_index < len(comments):
            i = self.current_index  # Get the current index
            try:
                print(f"Processing comment {i + 1}/{len(comments)}: {comments[i]['id']}")  # Log progress

                # Process comment text with spaCy NER
                # ner_companies_spacy = self.match_companies_ner_spacy(comments[i]["text"])
                # print(f"spaCy NER results: {ner_companies_spacy}")

                # Process comment text with Hugging Face NER
                ner_companies_hf = self.match_companies_ner_hf(comments[i]["text"])
                print(f"Hugging Face NER results: {ner_companies_hf}")

                # If no results from either model, reset models and retry
                # if not ner_companies_spacy and not ner_companies_hf:
                if not ner_companies_hf:
                    print("No NER results from either model, resetting models...")
                    self.reset_models()  # Reload models
                    continue  # Retry the same comment

                # Add classified company data to the results list
                classified_companies.append({
                    "comment_id": comments[i]["id"],
                    # "ner_companies_spacy": ner_companies_spacy,
                    "ner_companies_hf": ner_companies_hf,
                    "comment_text": comments[i]["text"]
                })

                # Save intermediate results every 10 comments
                if (i + 1) % 10 == 0:
                    temp_output_path = f'temp_classified_companies_{i + 1}.csv'
                    pd.json_normalize(classified_companies).to_csv(temp_output_path, index=False)
                    print(f"Intermediate results saved to {temp_output_path}.")

                # Reload models periodically based on the reset interval
                if (i + 1) % reset_interval == 0:
                    self.reset_models()

                # Force garbage collection to manage memory
                gc.collect()

                self.current_index += 1  # Move to the next comment

            except Exception as e:
                # Log errors for the current comment and move to the next
                print(f"Unhandled error with comment {i + 1}/{len(comments)}: {e}")
                self.current_index += 1

        # Final save of all classified data
        try:
            output_path = r'C:\Users\anura\Documents\PyProjects\FoolAround\SentimentScraper_Project\SupportingFiles\classified_companies_vi.csv'
            pd.json_normalize(classified_companies).to_csv(output_path, index=False)
            print(f"Classification results saved to {output_path}.")
        except Exception as e:
            print(f"Error saving classified data: {e}")

        return classified_companies

    def reset_models(self):
        """
        Reload models to reset state and manage potential issues.
        """
        print("Reloading models to reset state...")  # Log model reset
        # self.nlp = spacy.load("en_core_web_md")  # Reload spaCy model
        self.hf_ner = pipeline("ner",  # Reload Hugging Face pipeline
                                model='dbmdz/bert-large-cased-finetuned-conll03-english',
                                grouped_entities=True)
        gc.collect()  # Force garbage collection to manage memory
