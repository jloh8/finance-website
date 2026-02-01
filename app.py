import streamlit as st
import feedparser
from datetime import datetime
import time
import requests
from urllib.parse import quote
import json

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
    .news-item {
        background-color: white;
        padding: 0.8rem 1rem;
        margin-bottom: 0.5rem;
        border-radius: 5px;
        border-left: 3px solid #0066cc;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: all 0.2s ease;
        cursor: pointer;
    }
    .news-item:hover {
        background-color: #f0f7ff;
        transform: translateX(5px);
        box-shadow: 0 2px 8px rgba(0,102,204,0.2);
    }
    .news-title {
        font-size: 1rem;
        color: #0066cc;
        flex: 1;
        margin-right: 1rem;
        text-decoration: none;
    }
    .news-title:hover {
        text-decoration: underline;
    }
    .news-date {
        color: #888;
        font-size: 0.85rem;
        white-space: nowrap;
        min-width: 120px;
        text-align: right;
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
    .suggestion-box {
        background-color: #f0f7ff;
        padding: 0.8rem;
        border-radius: 5px;
        border-left: 3px solid #0066cc;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Company name to ticker mapping (common stocks)
COMPANY_TICKER_MAP = {
    # Tech
    'apple': 'AAPL',
    'microsoft': 'MSFT',
    'google': 'GOOGL',
    'alphabet': 'GOOGL',
    'amazon': 'AMZN',
    'meta': 'META',
    'facebook': 'META',
    'tesla': 'TSLA',
    'nvidia': 'NVDA',
    'amd': 'AMD',
    'advanced micro devices': 'AMD',
    'intel': 'INTC',
    'netflix': 'NFLX',
    'adobe': 'ADBE',
    'salesforce': 'CRM',
    'oracle': 'ORCL',
    'ibm': 'IBM',
    'cisco': 'CSCO',
    'qualcomm': 'QCOM',
    'broadcom': 'AVGO',
    
    # Finance
    'jpmorgan': 'JPM',
    'jp morgan': 'JPM',
    'bank of america': 'BAC',
    'wells fargo': 'WFC',
    'goldman sachs': 'GS',
    'morgan stanley': 'MS',
    'citigroup': 'C',
    'berkshire hathaway': 'BRK.B',
    'berkshire': 'BRK.B',
    'visa': 'V',
    'mastercard': 'MA',
    'paypal': 'PYPL',
    'american express': 'AXP',
    
    # Retail & Consumer
    'walmart': 'WMT',
    'target': 'TGT',
    'costco': 'COST',
    'home depot': 'HD',
    "lowe's": 'LOW',
    'nike': 'NKE',
    'mcdonalds': 'MCD',
    "mcdonald's": 'MCD',
    'starbucks': 'SBUX',
    'coca cola': 'KO',
    'coca-cola': 'KO',
    'pepsi': 'PEP',
    'pepsico': 'PEP',
    'procter gamble': 'PG',
    'procter & gamble': 'PG',
    
    # Pharma & Healthcare
    'pfizer': 'PFE',
    'johnson & johnson': 'JNJ',
    'johnson and johnson': 'JNJ',
    'abbvie': 'ABBV',
    'merck': 'MRK',
    'eli lilly': 'LLY',
    'bristol myers': 'BMY',
    'unitedhealth': 'UNH',
    
    # Automotive
    'ford': 'F',
    'general motors': 'GM',
    'gm': 'GM',
    'toyota': 'TM',
    'honda': 'HMC',
    'ferrari': 'RACE',
    'lucid': 'LCID',
    'rivian': 'RIVN',
    'nio': 'NIO',
    
    # Energy
    'exxon': 'XOM',
    'exxonmobil': 'XOM',
    'chevron': 'CVX',
    'conocophillips': 'COP',
    'shell': 'SHEL',
    'bp': 'BP',
    
    # Other
    'disney': 'DIS',
    'boeing': 'BA',
    'lockheed martin': 'LMT',
    'caterpillar': 'CAT',
    'deere': 'DE',
    'john deere': 'DE',
    '3m': 'MMM',
    'general electric': 'GE',
    'ge': 'GE',
    
    # ETFs & Indexes
    'spy': 'SPY',
    's&p 500': 'SPY',
    'sp500': 'SPY',
    'nasdaq': 'QQQ',
    'qqq': 'QQQ',
    'dow jones': 'DIA',
    'dia': 'DIA',
}

def find_ticker(search_term):
    """Convert company name to ticker symbol"""
    search_term = search_term.lower().strip()
    
    # First check if it's already a ticker (all caps, short)
    if search_term.upper() == search_term and len(search_term) <= 5:
        return search_term.upper(), None
    
    # Check exact match in dictionary
    if search_term in COMPANY_TICKER_MAP:
        return COMPANY_TICKER_MAP[search_term], search_term
    
    # Check partial match
    for company, ticker in COMPANY_TICKER_MAP.items():
        if search_term in company or company in search_term:
            return ticker, company
    
    # Try Yahoo Finance search API
    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={quote(search_term)}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=3)
        data = response.json()
        
        if 'quotes' in data and len(data['quotes']) > 0:
            top_result = data['quotes'][0]
            ticker = top_result.get('symbol', '')
            name = top_result.get('longname', '') or top_result.get('shortname', '')
            return ticker, name
    except:
        pass
    
    # Return as-is if nothing found
    return search_term.upper(), None

@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_yahoo_finance_news():
    """Fetch top news from Yahoo Finance RSS feed"""
    try:
        rss_url = "https://finance.yahoo.com/news/rssindex"
        feed = feedparser.parse(rss_url)
        
        news_items = []
        for entry in feed.entries[:30]:  # Get top 30 news
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
        for entry in feed.entries[:40]:  # Get top 40 news for ticker
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
                'currency': result['meta'].get('currency', 'USD'),
                'name': result['meta'].get('longName', ticker)
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
        "🔍 Search by company name or ticker (e.g., Tesla, AAPL, Microsoft, NVDA)",
        placeholder="Enter company name or ticker symbol...",
        label_visibility="collapsed"
    )

with col2:
    search_button = st.button("Search", use_container_width=True, type="primary")

with col3:
    clear_button = st.button("Clear", use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)

# Handle clear button
if clear_button:
    ticker_input = ""
    st.rerun()

# Determine what to show
show_ticker_news = False
resolved_ticker = None
company_name = None

if (search_button or ticker_input) and ticker_input:
    # Convert company name to ticker
    resolved_ticker, company_name = find_ticker(ticker_input)
    show_ticker_news = True
    
    # Show suggestion if company name was found
    if company_name and company_name != ticker_input.lower():
        st.markdown(f"""
        <div class='suggestion-box'>
            💡 Found: <strong>{company_name.title()}</strong> → Ticker: <strong>{resolved_ticker}</strong>
        </div>
        """, unsafe_allow_html=True)

# Display news based on mode
if show_ticker_news and resolved_ticker:
    ticker = resolved_ticker.upper().strip()
    
    # Display ticker badge
    st.markdown(f"<div class='ticker-badge'>📊 {ticker}</div>", unsafe_allow_html=True)
    
    # Get stock price
    stock_data = get_stock_price(ticker)
    if stock_data:
        st.subheader(stock_data['name'])
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
            # Format date to be more compact
            try:
                from datetime import datetime
                date_obj = datetime.strptime(item['published'], '%a, %d %b %Y %H:%M:%S %z')
                formatted_date = date_obj.strftime('%b %d, %Y')
            except:
                formatted_date = item['published'][:12] if item['published'] else 'N/A'
            
            st.markdown(f"""
            <a href="{item['link']}" target="_blank" style="text-decoration: none;">
                <div class='news-item'>
                    <div class='news-title'>{idx}. {item['title']}</div>
                    <div class='news-date'>📅 {formatted_date}</div>
                </div>
            </a>
            """, unsafe_allow_html=True)
    else:
        st.warning(f"No news found for ticker '{ticker}'. Try another ticker or check the spelling.")
        st.info("💡 Tip: Try typing the company name (e.g., 'Tesla', 'Apple', 'Microsoft')")

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
            # Format date to be more compact
            try:
                from datetime import datetime
                date_obj = datetime.strptime(item['published'], '%a, %d %b %Y %H:%M:%S %z')
                formatted_date = date_obj.strftime('%b %d, %Y')
            except:
                formatted_date = item['published'][:12] if item['published'] else 'N/A'
            
            st.markdown(f"""
            <a href="{item['link']}" target="_blank" style="text-decoration: none;">
                <div class='news-item'>
                    <div class='news-title'>{idx}. {item['title']}</div>
                    <div class='news-date'>📅 {formatted_date}</div>
                </div>
            </a>
            """, unsafe_allow_html=True)
    else:
        st.warning("No news items found. Please try refreshing.")

# Sidebar
with st.sidebar:
    st.header("ℹ️ About")
    st.write("This app displays the latest top news from Yahoo Finance.")
    st.write("Search by **company name** or **ticker symbol**!")
    
    st.header("📊 Features")
    st.write("✅ Company name search")
    st.write("✅ General market news")
    st.write("✅ Ticker-specific news")
    st.write("✅ Real-time stock prices")
    st.write("✅ Auto-refresh every 5 min")
    
    st.header("💡 Try These")
    st.write("**Company Names:**")
    st.write("Tesla, Apple, Microsoft, Amazon, Google, Meta, Netflix, Nvidia")
    
    st.write("**Or Tickers:**")
    popular_tickers = ["AAPL", "TSLA", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "AMD", "NFLX", "SPY"]
    
    cols = st.columns(2)
    for i, ticker in enumerate(popular_tickers):
        with cols[i % 2]:
            if st.button(ticker, use_container_width=True, key=f"sidebar_{ticker}"):
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