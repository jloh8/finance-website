import streamlit as st
import feedparser
from datetime import datetime
import time

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

# Header
st.markdown("<h1 class='header-title'>📈 Yahoo Finance Top News</h1>", unsafe_allow_html=True)

# Fetch news
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

# Display news
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
    st.write("The news feed updates every 5 minutes automatically.")
    
    st.header("📊 Stats")
    st.metric("Total News Items", len(news_items))
    st.metric("Auto-refresh", "5 minutes")
    
    st.header("🔗 Source")
    st.write("Data from [Yahoo Finance](https://finance.yahoo.com)")
    
    # Auto-refresh toggle
    st.header("⚙️ Settings")
    auto_refresh = st.checkbox("Auto-refresh page", value=False)
    
    if auto_refresh:
        st.info("Page will refresh every 5 minutes")
        time.sleep(300)
        st.rerun()