'''
Authors: Anurag Purker, & GPT
'''

import csv
import praw
import re
import pandas as pd
# import openai
# import os
# import orjson
from datetime import datetime
import praw
import re
import json
from datetime import datetime
from fuzzywuzzy import fuzz

class RedditFinancialScraper:

    def __init__(self, client_id, client_secret, user_agent, ticker_file):
        self.reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)
        self.stock_regex = r'\b[A-Z]{2,5}(?:\.[A-Za-z]+)?\b'
        self.ticker_list = self.load_ticker_list(ticker_file)

    def load_ticker_list(self, ticker_file):
        with open(ticker_file, 'r') as file:
            ticker_data = json.load(file)
        ticker_dict = {item["ticker"]: item["title"] for item in ticker_data.values()}
        return ticker_dict

    def get_posts(self, subreddit,category='hot',limit=10):
        ### try to write off file before just dumping data
        return getattr(self.reddit.subreddit(subreddit), category)(limit=limit)
    
    def find_symbols(self, text):
        pattern = self.stock_regex
        found_tickers = set(re.findall(pattern, text))
        matched_companies = self.match_companies(text)
        for company in matched_companies:
            found_tickers.add(company)
        valid_tickers = {ticker: (ticker.upper() in self.ticker_list.keys()) if ticker.upper() in self.ticker_list.keys() else False for ticker in found_tickers}
        return valid_tickers

    def extract_post_data(self, post):
        post_data = {
            "post_title": post.title,
            "post_date": post.created_utc,  
            "post_body": post.selftext,
            "comments": self.extract_comments_data(post.comments)
        }
        post_data['relevant_tickers'] = self.find_symbols(post_data['post_body'])
        return post_data

    def extract_comments_data(self, comments):
        comments.replace_more(limit=None)
        comment_data = []
        for comment in comments.list():
            comment_dict = {
                "comment_date": comment.created_utc,
                "comment_body": comment.body,
            }
            comment_dict['relevant_tickers'] = self.find_symbols(comment_dict['comment_body'])
            comment_data.append(comment_dict)
        return comment_data

    def most_discussed_org(self, subreddit,limit=10,category='hot'):
        results = []
        for post in self.get_posts(subreddit, category, limit=limit):
            post_data = self.extract_post_data(post)
            results.append(post_data)
        return results
    
    def most_discussed_org_from_sticky(self, subreddit, limit=10):
        results = []
        for post in self.get_posts(subreddit, category='hot', limit=limit):
            if post.stickied:
                post_data = self.extract_post_data(post)
                results.append(post_data)
                break  # Stop after processing the first stickied post
        return results
    def match_companies(self, comment_text):
        sec_dict = self.ticker_list
        relevant_tickers = []
        comment_words = [x.lower() for x in comment_text.split(" ")]
        corporate_identifiers = ["inc", "inc.", "corp", "corp.", "corporation", "company", "co", "co.", "s.a.", "group", "plc", 
                            "ltd", "ltd.", "limited", "ag", "nv", "holdings", "lp", "lp.", "sa", "sp.a", "se", "trust", "srl", 
                            "s.r.l.", "llc", "llc.", "etf", "reit", "partners", "capital", "industries", "international", "services", 
                            "spc", "gmbh", "bhd", "pte", "pte.", "sas", "societe", "limited.", "llp", "llp.", "s.a.b.", "kabushiki kaisha", 
                            "s.p.a.", "aktiengesellschaft", "oyj", "s.a.s.", "unlimited", "s.c.a.", "pte ltd", "public limited company", "s.a.p.i. de c.v.", ",", "."]

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
                    pass
                    # Fuzzy matching
                    # similarity_score = fuzz.token_set_ratio(company_name, comment_text)
                    # if similarity_score > 70:
                    #     relevant_tickers.append(ticker)
                    #     print(f"Found fuzzy reference to {ticker} ({company_name}) in the comment: {comment_text}.")
                    #     writer.writerow({
                    #         "Ticker": ticker,
                    #         "Company Name": company_name,
                    #         "Match Type": "Fuzzy Match",
                    #         "Comment Words": " ".join(comment_words),
                    #         "Company Words": " ".join(company_words),
                    #         "Comment": comment_text,
                    #         "Similarity Score": similarity_score
                    #     })
            return relevant_tickers



    # def match_companies(self, comment_text):
    #     corporate_identifiers = ["inc", "inc.", "corp", "corp.", "corporation",
    #                               "company", "co", "co.", "s.a.", "group", "plc", 
    #                               "ltd", "ltd.", "limited", "ag", "nv", "holdings", 
    #                               "lp", "lp.", "sa", "sp.a", "se", "trust", "srl", "s.r.l.", 
    #                               "llc", "llc.", "etf", "reit", "partners", "capital", 
    #                               "industries", "international", "services", "spc", "gmbh", 
    #                               "bhd", "pte", "pte.", "sas", "societe", "limited.", "llp", 
    #                               "llp.", "s.a.b.", "kabushiki kaisha", "s.p.a.", "aktiengesellschaft", 
    #                               "oyj", "s.a.s.", "unlimited", "s.c.a.", "pte ltd", 
    #                               "public limited company", "s.a.p.i. de c.v.", ",", "."]
    #     sec_dict = self.ticker_list
    #     relevant_tickers = []
    #     comment_words = [x.lower() for x in comment_text.split(" ")]

    #     for ticker, company_name in sec_dict.items():
    #         company_words = [x.lower() for x in company_name.split(" ")]
    #         # Remove common corporate structure words
    #         while company_words and company_words[-1].lower() in corporate_identifiers:
    #             company_words = company_words[:-1]

    #         with open('fuzzymatchlog.txt', 'a', encoding='utf-8') as f:
    #             f.write(f"{str(company_words)}\n{comment_words}\n")

    #         # Check for exact match
    #         if all(word in comment_words for word in company_words):
    #             relevant_tickers.append(ticker)
    #             print(f"Found exact reference to {ticker} ({company_name}) in the comment: {comment_text}.")
    #             with open('fuzzymatchlog.txt', 'a', encoding='utf-8') as f:
    #                 f.write(f"Found exact reference to {ticker} ({company_name}) in the comment: {comment_text}.\n")
    #         else:
    #             # Fuzzy matching
    #             similarity_score = fuzz.token_set_ratio(company_name, comment_text)
    #             if similarity_score > 65:
    #                 relevant_tickers.append(ticker)
    #                 print(f"Found fuzzy reference to {ticker} ({company_name}) in the comment: {comment_text}.")
    #                 with open('fuzzymatchlog.txt', 'a', encoding='utf-8') as f:
    #                     f.write(f"Found fuzzy reference to {ticker} ({company_name}) in the comment: {comment_text}.\n")

            return relevant_tickers
    # def match_companies(self, comment_text):
    #     sec_dict = self.ticker_list
    #     relevant_tickers = []
    #     i=0
    #     for ticker, company_name in sec_dict.items():
    #         similarity_score = fuzz.token_set_ratio(company_name, comment_text)
    #         if similarity_score > 65:
    #             relevant_tickers.append(ticker)
    #             print(f"{i}: Found reference to {ticker} ({company_name}) in the comment: {comment_text}.")
    #             with open('fuzzymatchlog.txt','a',encoding='utf-8') as f:
    #                 f.write(f"{i}: Found reference to {ticker} ({company_name}) in the comment: {comment_text}.")
    #                 i +=1
                    
    #     return relevant_tickers

# '''
# Authors: Anurag Purker, & GPT
# '''
# import praw/9*+/**98+76
# import re
# import pandas as pd
# import openai
# import os
# import json
# from datetime import datetime
# import praw
# import re
# import json
# from datetime import datetime

# class RedditFinancialScraper:
#     def __init__(self, client_id, client_secret, user_agent, ticker_file):
#         self.reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)
#         self.stock_regex = r'\b[A-Z]{2,5}(?:\.[A-Za-z]+)?\b'
#         self.ticker_list = self.load_ticker_list(ticker_file)

#     def load_ticker_list(self, ticker_file):
#         with open(ticker_file, 'r') as file:
#             ticker_data = json.load(file)
#         return set([ticker['ticker'] for ticker in ticker_data.values()])

#     def get_posts(self, subreddit,category='hot',limit=10):
#         return getattr(self.reddit.subreddit(subreddit), category)(limit=limit)

#     def find_symbols(self, text):
#         pattern = self.stock_regex
#         found_tickers = set(re.findall(pattern, text))
#         valid_tickers = {ticker: (ticker.upper() in self.ticker_list) if ticker.upper() in self.ticker_list else False for ticker in found_tickers}
#         return valid_tickers

#     def extract_post_data(self, post):
#         post_data = {
#             "post_title": post.title,
#             "post_date": post.created_utc,
#             "post_body": post.selftext,
#             "comments": self.extract_comments_data(post.comments)
#         }
#         post_data['relevant_tickers'] = self.find_symbols(post_data['post_body'])
#         return post_data

#     def extract_comments_data(self, comments):
#         comments.replace_more(limit=None)
#         comment_data = []
#         for comment in comments.list():
#             # if isinstance(comment, praw.models.MoreComments):
#             #     continue
#             comment_dict = {
#                 "comment_date": comment.created_utc,
#                 "comment_body": comment.body,
#                 # "relevant_tickers": list(self.find_symbols(comment.body))
#             }
#             comment_dict['relevant_tickers'] = self.find_symbols(comment_dict['comment_body'])
#             comment_data.append(comment_dict)
#         return comment_data

#     def most_discussed_org(self, subreddit,limit=10,category='hot'):
#         results = []
#         for post in self.get_posts(subreddit, category, limit=limit):
#             post_data = self.extract_post_data(post)
#             results.append(post_data)
#         return results
    
#     def most_discussed_org_from_sticky(self, subreddit, limit=10):
#         results = []
#         for post in self.get_posts(subreddit, category='hot', limit=limit):
#             if post.stickied:
#                 post_data = self.extract_post_data(post)
#                 results.append(post_data)
#                 break  # Stop after processing the first stickied post
#         return results
    
#     def match_companies(self, comment_text, ticker_dict):
        
#         if ticker_dict is None:
#             ticker_dict = self.ticker_list
#         sec_dict = {v: k for k, v in self.ticker_list.items()}
        
#         relevant_tickers = []
#         for ticker, company_name in sec_dict.items():
#             similarity_score = fuzz.partial_ratio(company_name.lower(), comment_text.lower())
#             print(similarity_score)
#             if similarity_score > 80:
#             relevant_tickers.append(ticker)
#             print(f"Found reference to {ticker} ({company_name}) in the comment.")
#         return relevant_tickers
        
        
        
        
        
        
        
        
        
        
#         if ticker_dict is None:
#             ticker_dict = self.ticker_list
#         sec_dict = {v: k for k, v in ticker_dict.items()}
        
#         relevant_companies = []
#         for ticker, company_name in sec_dict.items():
#             similarity_score = fuzz.partial_ratio(company_name.lower(), comment_text.lower())
#             sim = fuzz.ratio(comment_text.lower(), company_name.lower())
#             print(similarity_score)
#             print(sim)
#             if similarity_score > 80:
#                 relevant_companies.append(company_name)
#                 print(f"Found reference to {ticker} ({company_name}) in the comment.")
#         return relevant_companies
# # class RedditFinancialScraper:
# #     def __init__(self, client_id, client_secret, user_agent, ticker_file):
# #         self.reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)
# #         self.stock_regex = r'\b[A-Z]{2,5}(?:\.[A-Za-z]+)?\b'
# #         self.ticker_list = self.load_ticker_list(ticker_file)

# #     def load_ticker_list(self, ticker_file):
# #         with open(ticker_file, 'r') as file:
# #             ticker_data = json.load(file)
# #         return set([ticker['ticker'] for ticker in ticker_data.values()])

# #     def get_posts(self, subreddit, category='hot', limit=10):
# #         return getattr(self.reddit.subreddit(subreddit), category)(limit=limit)

# #     def find_symbols(self, text):
# #         pattern = self.stock_regex
# #         found_tickers = set(re.findall(pattern, text))
# #         return found_tickers

# #     def extract_post_data(self, post):
# #         post_data = {
# #             "post_title": post.title,
# #             "post_date": post.created_utc,
# #             "post_body": post.selftext,
# #             "comments": self.extract_comments_data(post.comments)
# #         }
# #         post_data['relevant_tickers'] = list(self.find_symbols(post_data['post_body']))
# #         return post_data

# #     def extract_comments_data(self, comments):
# #         comments.replace_more(limit=None)
# #         comment_data = []
# #         for comment in comments.list():
# #             comment_dict = {
# #                 "comment_date": comment.created_utc,
# #                 "comment_body": comment.body,
# #                 "relevant_tickers": list(self.find_symbols(comment.body))
# #             }
# #             comment_data.append(comment_dict)
# #         return comment_data

# #     def most_discussed_org(self, subreddit, limit=10, category='hot'):
# #         results = []
# #         for post in self.get_posts(subreddit, category, limit=limit):
# #             post_data = self.extract_post_data(post)
# #             results.append(post_data)
# #         return results

# #     def most_discussed_org_from_sticky(self, subreddit, limit=10):
# #         results = []
# #         for post in self.get_posts(subreddit, category='hot', limit=limit):
# #             if post.stickied:
# #                 post_data = self.extract_post_data(post)
# #                 results.append(post_data)
# #                 break  # Stop after processing the first stickied post
# #         return results