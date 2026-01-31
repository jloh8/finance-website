#!/usr/bin/env python3
"""
News Slideshow Generator
Fetches real-time news and creates an interactive HTML slideshow
"""
import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Market Front Page", layout="wide")

# --- 1. Top Market Bar (The "Ticker Tape") ---
st.write("### Market Summary")
indices = {
    "^GSPC": "S&P 500",
    "^DJI": "Dow 30",
    "^IXIC": "Nasdaq",
    "BTC-USD": "Bitcoin",
    "GC=F": "Gold"
}

# Create columns for the top bar
cols = st.columns(len(indices))

for i, (symbol, name) in enumerate(indices.items()):
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="2d")
    
    if len(data) >= 2:
        current_price = data['Close'].iloc[-1]
        prev_price = data['Close'].iloc[-2]
        change = current_price - prev_price
        pct_change = (change / prev_price) * 100
        
        cols[i].metric(name, f"{current_price:,.2f}", f"{pct_change:+.2f}%")

st.divider()

# --- 2. Main News Section ---
st.header("🌍 Top Stories")

# We use a general search term like "Finance" or "Market" to get broad front-page news
try:
    search = yf.Search("Stock Market", max_results=12)
    top_news = search.news
except:
    top_news = []

if top_news:
    # Display news in a grid (3 columns)
    for i in range(0, len(top_news), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(top_news):
                article = top_news[i + j]
                with cols[j]:
                    # Display news card
                    st.subheader(article.get('title', 'Headline'))
                    st.caption(f"Source: {article.get('publisher')} | {datetime.fromtimestamp(article.get('providerPublishTime', 0)).strftime('%Y-%m-%d')}")
                    
                    # If there's a thumbnail/image, display it (some news items have them)
                    if 'thumbnail' in article and 'resolutions' in article['thumbnail']:
                        st.image(article['thumbnail']['resolutions'][0]['url'], use_container_width=True)
                    
                    st.write(f"[Read Full Story]({article.get('link')})")
                    st.write("---")
else:
    st.info("No top stories found at the moment. Please refresh.")

# --- 3. Sidebar: Trending Tickers ---
st.sidebar.header("🔥 Trending Now")
trending_symbols = ["NVDA", "TSLA", "AAPL", "MSFT", "AMZN"]
for sym in trending_symbols:
    t = yf.Ticker(sym)
    price = t.history(period="1d")['Close'].iloc[-1]
    st.sidebar.write(f"**{sym}**: ${price:,.2f}")