"""
Authors: Anurag Purker

"""
import praw
import json
import gc
from transformers import pipeline
import pandas as pd
from fuzzywuzzy import fuzz
import os

class RedditScraper:
    def __init__(self, client_id, client_secret, user_agent, ticker_list_file):
        # Initialize PRAW (Python Reddit API Wrapper)
        self.reddit = praw.Reddit(client_id=client_id,  # Reddit API client ID
                                  client_secret=client_secret,  # Reddit API client secret
                                  user_agent=user_agent)  # User agent for the API

        # Load ticker list from file
        with open(ticker_list_file, 'r') as file:
            self.ticker_list = json.load(file)  # Load JSON data from file

        # Load Hugging Face pipeline for NER
        self.hf_ner = pipeline("ner",  # Use "ner" pipeline for Named Entity Recognition
                                model='dbmdz/bert-large-cased-finetuned-conll03-english',  # Pretrained BERT model
                                grouped_entities=True)  # Group consecutive entity tokens

        self.sentiment_pipeline = pipeline("sentiment-analysis")
        

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
            print(f"Sentiment analysis error: {e}")  # Log errors if sentiment analysis fails
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
            print(f"Hugging Face error: {e}")  # Log errors if Hugging Face pipeline fails
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
                    "type": "post"  # Indicate this is a post
                })

                # Expand and add all comments from the submission
                submission.comments.replace_more(limit=None)  # Expand all comments
                for comment in submission.comments.list():
                    data.append({
                        "id": comment.id,
                        "text": comment.body,
                        "type": "comment"  # Indicate this is a comment
                    })

            return data
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

                # Process comment text with Hugging Face NER
                ner_companies_hf = self.match_companies_ner_hf(comments[i]["text"])
                print(f"Hugging Face NER results: {ner_companies_hf}")

                # Process comment text with Hugging Face sentiment analysis
                sentiment = self.analyze_sentiment(comments[i]["text"])
                print(f"Sentiment analysis results: {sentiment}")

                print(comments[i]["text"])

                # Update the comment with NER and sentiment results
                comments[i]["ner_companies_hf"] = ner_companies_hf
                comments[i]["Sentiment_score"] = sentiment

                classified_companies.append({
                    "comment_id": comments[i]["id"],
                    "ner_companies_hf": ner_companies_hf,
                    "comment_text": comments[i]["text"],
                    'Sentiment_score': sentiment
                })

                # Save intermediate results every 10 comments
                if (i + 1) % 10 == 0:
                    temp_output_path = f'temp_classified_companies_{i + 1}.csv'
                    pd.json_normalize(classified_companies).to_csv(temp_output_path, index=False)
                    print(f"Intermediate results saved to {temp_output_path}.")

                # Force garbage collection to manage memory
                gc.collect()

                self.current_index += 1  # Move to the next comment

            except Exception as e:
                # Log errors for the current comment and move to the next
                print(f"Unhandled error with comment {i + 1}/{len(comments)}: {e}")
                self.current_index += 1

        # Final save of all classified data
        try:
            output_path = os.path.join(repo_path, 'OutputFiles/classified_companies_vi.csv')
            print(f"Classification results saved to {output_path}.")
        except Exception as e:
            print(f"Error saving classified data: {e}")
            repo_path = os.getcwd()  # Get the current working directory (repository path)
            

        # Save the updated comments with NER and sentiment results
        try:
            comments_output_path = os.path.join(repo_path, 'OutputFiles/comments_with_classification.json')
            with open(comments_output_path, 'w') as f:
                json.dump(comments, f, indent=4)
            print(f"Updated comments saved to {comments_output_path}.")
        except Exception as e:
            print(f"Error saving updated comments: {e}")

        return classified_companies

    def reset_models(self):
        """
        Reload models to reset state and manage potential issues.
        """
        print("Reloading models to reset state...")  # Log model reset
        self.hf_ner = pipeline("ner",  # Reload Hugging Face pipeline
                                model='dbmdz/bert-large-cased-finetuned-conll03-english',
                                grouped_entities=True)
        gc.collect()  # Force garbage collection to manage memory
