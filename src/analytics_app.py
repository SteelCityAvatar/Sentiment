import streamlit as st
import pandas as pd
import requests
from wordcloud import WordCloud
import datetime

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Reddit Financial Sentiment EDA", layout="wide")
st.title("Reddit Financial Sentiment EDA & Visualization")

@st.cache_data

def get_companies():
    r = requests.get(f"{API_URL}/companies")
    return r.json()["companies"]

@st.cache_data

def get_sentiments():
    r = requests.get(f"{API_URL}/sentiments")
    return r.json()["sentiments"]

@st.cache_data

def get_comments(companies, sentiments, start_date, end_date, sample=1000):
    params = {
        "companies": companies,
        "sentiments": sentiments,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "sample": sample
    }
    r = requests.get(f"{API_URL}/comments", params=params)
    return pd.DataFrame(r.json())

@st.cache_data

def get_mention_counts(companies, sentiments, start_date, end_date):
    params = {
        "companies": companies,
        "sentiments": sentiments,
        "start_date": str(start_date),
        "end_date": str(end_date)
    }
    r = requests.get(f"{API_URL}/mention_counts", params=params)
    return pd.DataFrame(r.json())

@st.cache_data

def get_time_series(companies, sentiments, start_date, end_date, freq='D'):
    params = {
        "companies": companies,
        "sentiments": sentiments,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "freq": freq
    }
    r = requests.get(f"{API_URL}/time_series", params=params)
    return pd.DataFrame(r.json())

def get_date_range():
    r = requests.get(f"{API_URL}/date_range")
    return r.json()["min_date"], r.json()["max_date"]

min_date_str, max_date_str = get_date_range()
min_date = datetime.datetime.strptime(min_date_str, "%Y-%m-%d").date()
max_date = datetime.datetime.strptime(max_date_str, "%Y-%m-%d").date()

date_range = st.sidebar.date_input(
    "Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Now date_range will always be a tuple/list of two dates
if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    st.warning("Please select a valid date range (start and end).")
    st.stop()

companies = get_companies()
sentiments = get_sentiments()

selected_companies = st.sidebar.multiselect("Select companies to analyze", companies, default=companies[:5])
selected_sentiments = st.sidebar.multiselect("Select sentiment labels", sentiments, default=['positive', 'negative'])

# Fetch filtered comments (sampled for performance)
df = get_comments(selected_companies, selected_sentiments, start_date, end_date, sample=1000)

if df.empty:
    st.warning("No company mentions found in the data.")
    st.stop()

st.subheader("Company Mention Counts by Sentiment")
mention_counts = get_mention_counts(selected_companies, selected_sentiments, start_date, end_date)
if not mention_counts.empty:
    mention_counts = mention_counts.set_index('company')
    st.bar_chart(mention_counts)
else:
    st.write("No data to display.")

st.subheader("Mentions Over Time (by Company)")
time_counts = get_time_series(selected_companies, selected_sentiments, start_date, end_date)
if not time_counts.empty:
    time_counts = time_counts.set_index('date')
    st.line_chart(time_counts)
else:
    st.write("No data to display.")

st.subheader("Word Cloud of Positive/Negative Comments")
for sentiment in ['positive', 'negative']:
    st.markdown(f"#### {sentiment.capitalize()} Comments Word Cloud")
    texts = ' '.join(df[df['sentiment_label'] == sentiment]['text'])
    if texts:
        wordcloud = WordCloud(width=800, height=300, background_color='white').generate(texts)
        st.image(wordcloud.to_array(), use_column_width=True)
    else:
        st.write(f"No {sentiment} comments to display.")

st.subheader("Sample Comments")
for sentiment in ['positive', 'negative']:
    st.markdown(f"#### {sentiment.capitalize()} Comments")
    sample = df[df['sentiment_label'] == sentiment].sample(n=min(5, len(df[df['sentiment_label'] == sentiment])), random_state=42)
    for _, row in sample.iterrows():
        st.write(f"**{row['company']}** | {row['date']} | Score: {row['sentiment_score']:.2f}")
        st.write(row['text'])
        st.markdown("---") 