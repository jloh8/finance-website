import streamlit as st
import feedparser
from datetime import datetime
import time
import requests
from urllib.parse import quote

# Page configuration
st.set_page_config(
    page_title="Yahoo Finance Top News",
    page_icon="📈",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .news-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        border-left: 4px solid #0066cc;
    }
    .news-title {
        font-size: 1.3rem;
        font-weight: bold;
        color: #0066cc;
        margin-bottom: 0.5rem;
    }
    .news-description {
        color: #555;
        margin: 0.5rem 0;
        line-height: 1.6;
    }
    .news-date {
        color: #888;
        font-size: 0.9rem;
        font-style: italic;
    }
    .header-title {
        text-align: center;
        color: #333;
        margin-bottom: 1rem;
    }
    .update-time {
        text-align: center;
        color: #666;
        font-size: 0.9rem;
        margin-bottom: 2rem;
    }
    .search-box {
        margin-bottom: 2rem;
    }
    .ticker-badge {
        background-color: #0066cc;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.9rem;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_yahoo_finance_news():
    """Fetch top news from Yahoo Finance RSS feed"""
    try:
        rss_url = "https://finance.yahoo.com/news/rssindex"
        feed = feedparser.parse(rss_url)
        
        news_items = []
        for entry in feed.entries[:15]:  # Get top 15 news
            # Clean description
            description = entry.get('summary', 'No description')
            description = description.replace('<p>', '').replace('</p>', '')
            
            news_items.append({
                'title': entry.get('title', 'No title'),
                'link': entry.get('link', '#'),
                'description': description[:300] + '...' if len(description) > 300 else description,
                'published': entry.get('published', '')
            })
        
        return news_items, datetime.now()
    except Exception as e:
        st.error(f"Error fetching news: {e}")
        return [], datetime.now()

@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_ticker_news(ticker):
    """Fetch news for a specific ticker from Yahoo Finance"""
    try:
        # Clean up ticker
        ticker = ticker.upper().strip()
        
        # Yahoo Finance RSS feed for specific ticker
        rss_url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
        feed = feedparser.parse(rss_url)
        
        news_items = []
        for entry in feed.entries[:20]:  # Get top 20 news for ticker
            # Clean description
            description = entry.get('summary', 'No description')
            description = description.replace('<p>', '').replace('</p>', '')
            
            news_items.append({
                'title': entry.get('title', 'No title'),
                'link': entry.get('link', '#'),
                'description': description[:300] + '...' if len(description) > 300 else description,
                'published': entry.get('published', '')
            })
        
        return news_items, datetime.now()
    except Exception as e:
        st.error(f"Error fetching ticker news: {e}")
        return [], datetime.now()

def get_stock_price(ticker):
    """Get current stock price from Yahoo Finance"""
    try:
        ticker = ticker.upper().strip()
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()
        
        if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
            result = data['chart']['result'][0]
            price = result['meta']['regularMarketPrice']
            prev_close = result['meta']['previousClose']
            change = price - prev_close
            change_pct = (change / prev_close) * 100
            
            return {
                'price': price,
                'change': change,
                'change_pct': change_pct,
                'currency': result['meta'].get('currency', 'USD')
            }
    except:
        pass
    return None

# Header
st.markdown("<h1 class='header-title'>📈 Yahoo Finance Top News</h1>", unsafe_allow_html=True)

# Search bar for ticker
st.markdown("<div class='search-box'>", unsafe_allow_html=True)
col1, col2, col3 = st.columns([3, 1, 1])

with col1:
    ticker_input = st.text_input(
        "🔍 Search for a stock ticker (e.g., AAPL, TSLA, MSFT, NVDA)",
        placeholder="Enter ticker symbol...",
        label_visibility="collapsed"
    )

with col2:
    search_button = st.button("Search Ticker", use_container_width=True, type="primary")

with col3:
    clear_button = st.button("Clear", use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)

# Handle clear button
if clear_button:
    ticker_input = ""
    st.rerun()

# Determine what to show
show_ticker_news = False
if search_button and ticker_input:
    show_ticker_news = True
elif ticker_input and not search_button:
    # Auto-search on Enter
    show_ticker_news = True

# Display news based on mode
if show_ticker_news and ticker_input:
    # Ticker-specific news
    ticker = ticker_input.upper().strip()
    
    # Display ticker badge
    st.markdown(f"<div class='ticker-badge'>📊 {ticker}</div>", unsafe_allow_html=True)
    
    # Get stock price
    stock_data = get_stock_price(ticker)
    if stock_data:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Price", f"${stock_data['price']:.2f}")
        with col2:
            st.metric("Change", f"${stock_data['change']:.2f}", 
                     delta=f"{stock_data['change_pct']:.2f}%")
        with col3:
            st.metric("Currency", stock_data['currency'])
        with col4:
            if st.button("🔄 Refresh Price"):
                st.cache_data.clear()
                st.rerun()
    
    st.markdown("---")
    
    # Fetch ticker news
    news_items, update_time = fetch_ticker_news(ticker)
    
    # Display update time
    st.markdown(f"<div class='update-time'>Last updated: {update_time.strftime('%Y-%m-%d %H:%M:%S')}</div>", 
                unsafe_allow_html=True)
    
    # Display ticker news
    if news_items:
        st.success(f"Found {len(news_items)} news articles for {ticker}")
        
        for idx, item in enumerate(news_items, 1):
            with st.container():
                st.markdown(f"""
                <div class='news-card'>
                    <div class='news-title'>{idx}. {item['title']}</div>
                    <div class='news-description'>{item['description']}</div>
                    <div class='news-date'>📅 {item['published']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"[Read full article →]({item['link']})")
                st.markdown("---")
    else:
        st.warning(f"No news found for ticker '{ticker}'. Try another ticker or check the spelling.")
        st.info("💡 Tip: Make sure to use the correct ticker symbol (e.g., AAPL for Apple, TSLA for Tesla)")

else:
    # General top news
    news_items, update_time = fetch_yahoo_finance_news()
    
    # Display update time
    st.markdown(f"<div class='update-time'>Last updated: {update_time.strftime('%Y-%m-%d %H:%M:%S')}</div>", 
                unsafe_allow_html=True)
    
    # Auto-refresh button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔄 Refresh News", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # Display general news
    if news_items:
        for idx, item in enumerate(news_items, 1):
            with st.container():
                st.markdown(f"""
                <div class='news-card'>
                    <div class='news-title'>{idx}. {item['title']}</div>
                    <div class='news-description'>{item['description']}</div>
                    <div class='news-date'>📅 {item['published']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"[Read full article →]({item['link']})")
                st.markdown("---")
    else:
        st.warning("No news items found. Please try refreshing.")

# Sidebar
with st.sidebar:
    st.header("ℹ️ About")
    st.write("This app displays the latest top news from Yahoo Finance.")
    st.write("Search for any stock ticker to get targeted news!")
    
    st.header("📊 Features")
    st.write("✅ General market news")
    st.write("✅ Ticker-specific news")
    st.write("✅ Real-time stock prices")
    st.write("✅ Auto-refresh every 5 min")
    
    st.header("💡 Popular Tickers")
    popular_tickers = ["AAPL", "TSLA", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "AMD", "NFLX", "SPY"]
    
    cols = st.columns(2)
    for i, ticker in enumerate(popular_tickers):
        with cols[i % 2]:
            if st.button(ticker, use_container_width=True):
                st.session_state.ticker_input = ticker
                st.rerun()
    
    st.header("🔗 Source")
    st.write("Data from [Yahoo Finance](https://finance.yahoo.com)")
    
    # Auto-refresh toggle
    st.header("⚙️ Settings")
    auto_refresh = st.checkbox("Auto-refresh page", value=False)
    
    if auto_refresh:
        st.info("Page will refresh every 5 minutes")
        time.sleep(300)
        st.rerun()