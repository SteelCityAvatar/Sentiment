import json
import pandas as pd

with open('OutputFiles/comments_with_classification.json') as f:
    data = json.load(f)

rows = []
for entry in data:
    date = pd.to_datetime(entry['date'], unit='s')
    text = entry['text']
    companies = entry.get('ner_companies_hf', [])
    scores = entry.get('Sentiment_score', [])
    if not scores or not companies:
        continue  # Skip if no sentiment or no companies
    scores = scores[0]
    if not scores:
        continue  # Skip if sentiment score list is empty
    top = max(scores, key=lambda x: x['score'])
    for company in companies:
        rows.append({
            'date': date,
            'company': company,
            'sentiment_label': top['label'],
            'sentiment_score': top['score'],
            'text': text
        })

df = pd.DataFrame(rows)
df.to_parquet('OutputFiles/comments_with_classification.parquet')
print("Conversion complete! Parquet file saved.") 