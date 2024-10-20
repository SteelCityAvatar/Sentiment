aimport fuzzywuzzy
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import sys
import json
base_dir = os.getcwd()
project_path = os.path.join(base_dir,'SentimentScraper_Project','src')
support_files = os.path.join(base_dir,'SentimentScraper_Project','SupportingFiles')
sys.path.append(project_path)
json_file_path = rf"{support_files}"+'\company_tickers.json'
import re
dict1={
                "comment_date": "2024-10-19T00:15:51",
                "comment_body": "Visa and Mastercard are great candidates for monthly DCA.",
                "relevant_tickers": {
                    "DCA": False,
                    "MA": True
                    }
            }

def match_companies(comment_text, sec_dict=ticker_list):
    sec_dict = ticker_list
    relevant_tickers = []
    i=0
    for ticker, company_name in sec_dict.items():
        similarity_score = fuzz.token_set_ratio(company_name.lower(), comment_text.lower())
        if company_name == 'VISA INC.':
            print(similarity_score)
        if similarity_score > 80:
            relevant_tickers.append(ticker)
            print(f"{i}: Found reference to {ticker} ({company_name}) in the comment: {comment_text}.")
            with open('fuzzymatchlog.txt','a',encoding='utf-8') as f:
                f.write(f"{i}: Found reference to {ticker} ({company_name}) in the comment: {comment_text}.")
                i +=1
                
    return relevant_tickers

def load_ticker_list( ticker_file):
    with open(ticker_file, 'r') as file:
        ticker_data = json.load(file)
    ticker_dict = {item["ticker"]: item["title"] for item in ticker_data.values()}
    return ticker_dict

json_file_path = rf"{support_files}"+'\company_tickers.json'
ticker_list = load_ticker_list(ticker_file=json_file_path)

match_companies(dict1['comment_body'])
str1 = "Got 50% potfolio in apple. Bought at $135. I got chance buy microsoft when it was $200 but i though it was too high at that time. For me, i prefer focusing into 2-3 company that have strong financial."
str2 = "MICROSOFT CORP"
afuzzywuzzy.fuzz.token_set_ratio(str1,str2)