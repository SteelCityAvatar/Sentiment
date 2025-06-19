from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from typing import List, Optional
import uvicorn
import os

app = FastAPI()

# Allow CORS for local Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load data once at startup (Parquet for speed)
parquet_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'OutputFiles', 'comments_with_classification.parquet')
df = pd.read_parquet(parquet_path)

@app.get("/companies")
def get_companies():
    companies = sorted(df['company'].unique().tolist())
    return {"companies": companies}

@app.get("/sentiments")
def get_sentiments():
    sentiments = sorted(df['sentiment_label'].unique().tolist())
    return {"sentiments": sentiments}

@app.get("/comments")
def get_comments(
    companies: Optional[List[str]] = Query(None),
    sentiments: Optional[List[str]] = Query(None),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sample: Optional[int] = 100
):
    dff = df.copy()
    if companies:
        dff = dff[dff['company'].isin(companies)]
    if sentiments:
        dff = dff[dff['sentiment_label'].isin(sentiments)]
    if start_date:
        dff = dff[dff['date'] >= pd.to_datetime(start_date)]
    if end_date:
        dff = dff[dff['date'] <= pd.to_datetime(end_date)]
    if sample and len(dff) > sample:
        dff = dff.sample(n=sample, random_state=42)
    # Convert date to string for JSON serialization
    dff['date'] = dff['date'].astype(str)
    return dff.to_dict(orient='records')

@app.get("/mention_counts")
def get_mention_counts(
    companies: Optional[List[str]] = Query(None),
    sentiments: Optional[List[str]] = Query(None),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    dff = df.copy()
    if companies:
        dff = dff[dff['company'].isin(companies)]
    if sentiments:
        dff = dff[dff['sentiment_label'].isin(sentiments)]
    if start_date:
        dff = dff[dff['date'] >= pd.to_datetime(start_date)]
    if end_date:
        dff = dff[dff['date'] <= pd.to_datetime(end_date)]
    counts = dff.groupby(['company', 'sentiment_label']).size().unstack(fill_value=0)
    return counts.reset_index().to_dict(orient='records')

@app.get("/time_series")
def get_time_series(
    companies: Optional[List[str]] = Query(None),
    sentiments: Optional[List[str]] = Query(None),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    freq: str = 'D'
):
    dff = df.copy()
    if companies:
        dff = dff[dff['company'].isin(companies)]
    if sentiments:
        dff = dff[dff['sentiment_label'].isin(sentiments)]
    if start_date:
        dff = dff[dff['date'] >= pd.to_datetime(start_date)]
    if end_date:
        dff = dff[dff['date'] <= pd.to_datetime(end_date)]
    ts = dff.groupby([pd.Grouper(key='date', freq=freq), 'company']).size().unstack(fill_value=0)
    ts.index = ts.index.astype(str)
    return ts.reset_index().to_dict(orient='records')

@app.get("/date_range")
def get_date_range():
    min_date = str(df['date'].min())[:10]
    max_date = str(df['date'].max())[:10]
    return {"min_date": min_date, "max_date": max_date}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 