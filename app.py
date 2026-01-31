import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import requests
from typing import List, Dict

# --- Custom CSS for dark theme ---
st.markdown("""
<style>
    /* Main app background */
    .stApp {
        background-color: #1c1c1e;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #2c2c2e;
        border-right: 1px solid #3a3a3c;
    }
    
    /* Input fields */
    .stTextInput input, .stDateInput input, .stSelectbox {
        background-color: #3a3a3c !important;
        border: 1px solid #48484a !important;
        color: #ffffff !important;
        border-radius: 4px !important;
        font-size: 16px !important;
        font-weight: 500 !important;
    }
    
    /* Headers */
    h1 {
        color: #ffffff !important;
        font-weight: 800 !important;
        letter-spacing: -1px !important;
    }
    
    h2, h3 {
        color: #e0e0e0 !important;
        font-weight: 600 !important;
    }
    
    /* News card styling */
    .news-card {
        background: linear-gradient(135deg, #2c2c2e 0%, #3a3a3c 100%);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #48484a;
        margin: 15px 0;
        transition: transform 0.3s ease;
    }
    
    .news-card:hover {
        transform: translateY(-5px);
        border-color: #667eea;
    }
    
    .news-title {
        color: #ffffff;
        font-size: 20px;
        font-weight: 700;
        margin-bottom: 10px;
        line-height: 1.4;
    }
    
    .news-description {
        color: #b0b0b0;
        font-size: 14px;
        line-height: 1.6;
        margin-bottom: 10px;
    }
    
    .news-meta {
        color: #8e8e93;
        font-size: 12px;
        display: flex;
        gap: 15px;
        align-items: center;
    }
    
    .news-source {
        color: #667eea;
        font-weight: 600;
    }
    
    .category-badge {
        background-color: rgba(102, 126, 234, 0.2);
        color: #667eea;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
    }
    
    /* Info boxes */
    .info-box {
        background: linear-gradient(135deg, #2c2c2e 0%, #3a3a3c 100%);
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #48484a;
        margin: 10px 0;
    }
    
    .metric-label {
        color: #b0b0b0;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 5px;
        font-weight: 600;
    }
    
    .metric-value {
        color: #ffffff;
        font-size: 24px;
        font-weight: 700;
    }
    
    .positive {
        color: #00ff00 !important;
    }
    
    .negative {
        color: #ff0000 !important;
    }
    
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .badge-success {
        background-color: rgba(0, 255, 0, 0.15);
        color: #00ff00;
        border: 1px solid rgba(0, 255, 0, 0.3);
    }
    
    /* Sidebar text */
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #2c2c2e;
        border: 1px solid #48484a;
        color: #ffffff;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #667eea;
        border-color: #667eea;
    }
</style>
""", unsafe_allow_html=True)

# --- Page Config ---
st.set_page_config(
    page_title="Market Hub - News & Stocks",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📊"
)

# --- Helper Functions ---
class NewsAPI:
    """Fetch news from various sources"""
    
    @staticmethod
    def get_sample_news() -> List[Dict]:
        """Return sample news data"""
        return [
            {
                'title': 'Partial Government Shutdown Begins as Funding Lapses',
                'description': 'Senate passed spending bills late Friday, but funding for dozens of federal agencies has still lapsed, triggering a partial shutdown.',
                'source': 'CBS News',
                'publishedAt': '2026-01-31T10:00:00Z',
                'url': '#',
                'category': 'Politics'
            },
            {
                'title': 'Federal Judge Denies Request to Block ICE Surge in Minnesota',
                'description': 'Minnesota officials sought temporary halt to deployment of 3,000 federal agents, claiming state sovereignty violations.',
                'source': 'New York Times',
                'publishedAt': '2026-01-31T09:00:00Z',
                'url': '#',
                'category': 'Politics'
            },
            {
                'title': 'Djokovic Shocks Sinner in Late-Night Australian Open Thriller',
                'description': 'Serbian star defeats world No. 2 in five-set battle, keeping his dream of a record 25th Grand Slam title alive.',
                'source': 'The Guardian',
                'publishedAt': '2026-01-31T08:00:00Z',
                'url': '#',
                'category': 'Sports'
            },
            {
                'title': 'Tech Giants Announce Major AI Partnerships',
                'description': 'Leading technology companies unveil collaborations aimed at advancing artificial intelligence research and applications.',
                'source': 'TechCrunch',
                'publishedAt': '2026-01-31T07:00:00Z',
                'url': '#',
                'category': 'Technology'
            },
            {
                'title': 'Global Markets Rally on Economic Data',
                'description': 'Stock markets worldwide show strong gains following positive employment and manufacturing reports.',
                'source': 'Bloomberg',
                'publishedAt': '2026-01-31T06:00:00Z',
                'url': '#',
                'category': 'Business'
            },
            {
                'title': 'Google Takes Down Invisible Network Using Your Phone\'s Internet',
                'description': 'Tech giant removes controversial feature that used device bandwidth without clear user consent.',
                'source': 'Android Central',
                'publishedAt': '2026-01-30T22:00:00Z',
                'url': '#',
                'category': 'Technology'
            },
            {
                'title': 'Judge Drops Death Penalty Charge Against Luigi Mangione',
                'description': 'Manhattan district attorney\'s office moves forward with murder charges but drops capital punishment.',
                'source': 'New York Times',
                'publishedAt': '2026-01-30T18:00:00Z',
                'url': '#',
                'category': 'Legal'
            },
            {
                'title': 'Galaxy S26 May Finally Have Answer to Scam Calls',
                'description': 'Samsung\'s upcoming flagship phone reportedly includes advanced AI-powered scam detection features.',
                'source': 'Android Authority',
                'publishedAt': '2026-01-30T14:00:00Z',
                'url': '#',
                'category': 'Technology'
            }
        ]
    
    @staticmethod
    def fetch_news(api_key: str = None, category: str = 'general') -> List[Dict]:
        """Fetch news from NewsAPI or return sample data"""
        if api_key:
            try:
                url = 'https://newsapi.org/v2/top-headlines'
                params = {
                    'apiKey': api_key,
                    'country': 'us',
                    'category': category,
                    'pageSize': 20
                }
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                if data['status'] == 'ok':
                    return data['articles']
            except:
                pass
        return NewsAPI.get_sample_news()

def format_time_ago(timestamp_str: str) -> str:
    """Format timestamp to relative time"""
    try:
        pub_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        now = datetime.now(pub_time.tzinfo)
        diff = now - pub_time
        
        hours = diff.total_seconds() / 3600
        if hours < 1:
            return f"{int(diff.total_seconds() / 60)} minutes ago"
        elif hours < 24:
            return f"{int(hours)} hours ago"
        else:
            return f"{int(hours / 24)} days ago"
    except:
        return "Recently"

# --- Sidebar ---
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    
    # Mode selection
    app_mode = st.selectbox(
        "📱 Select Mode",
        ["📰 News Dashboard", "📊 Stock Dashboard", "🔄 Combined View"],
        index=2
    )
    
    st.markdown("---")
    
    if app_mode in ["📊 Stock Dashboard", "🔄 Combined View"]:
        st.markdown("### 📊 Stock Settings")
        ticker_symbol = st.text_input(
            "🔍 Ticker Symbol",
            value="AAPL",
            help="Enter stock ticker (e.g., AAPL, TSLA, MSFT)"
        ).upper()
        
        timeframe = st.select_slider(
            "📈 Timeframe",
            options=["1M", "3M", "6M", "1Y", "5Y", "10Y", "Max"],
            value="1Y"
        )
        
        chart_interval = st.radio(
            "📊 Chart Interval",
            ["Daily", "Weekly", "Monthly"],
            index=0,
            horizontal=True
        )
    
    if app_mode in ["📰 News Dashboard", "🔄 Combined View"]:
        st.markdown("---")
        st.markdown("### 📰 News Settings")
        
        news_api_key = st.text_input(
            "🔑 NewsAPI Key (Optional)",
            type="password",
            help="Get free key from newsapi.org"
        )
        
        news_category = st.selectbox(
            "📑 Category",
            ["general", "business", "technology", "sports", "politics"],
            index=0
        )
        
        auto_refresh = st.checkbox("🔄 Auto-refresh news", value=False)
        if auto_refresh:
            refresh_interval = st.slider("Refresh interval (minutes)", 1, 60, 5)

# --- Header ---
st.markdown("""
<div style='padding: 20px 0; margin-bottom: 30px;'>
    <h1 style='margin: 0; font-size: 42px;'>🌐 MARKET HUB</h1>
    <p style='color: #888888; margin-top: 5px; font-size: 14px;'>
        Real-time news and stock market data in one place
    </p>
</div>
""", unsafe_allow_html=True)

# --- Main Content ---
if app_mode == "📰 News Dashboard":
    # News only mode
    st.markdown("## 📰 Latest News")
    
    with st.spinner('🔄 Loading news...'):
        news_data = NewsAPI.fetch_news(news_api_key if news_api_key else None, news_category)
    
    # Display news in cards
    for article in news_data:
        title = article.get('title', 'No title')
        description = article.get('description', '')
        source = article.get('source', {}).get('name', 'Unknown') if isinstance(article.get('source'), dict) else article.get('source', 'Unknown')
        published = article.get('publishedAt', '')
        category = article.get('category', 'News')
        
        time_ago = format_time_ago(published)
        
        st.markdown(f"""
        <div class='news-card'>
            <div style='display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;'>
                <span class='category-badge'>{category}</span>
                <span class='news-meta'>{time_ago}</span>
            </div>
            <div class='news-title'>{title}</div>
            <div class='news-description'>{description}</div>
            <div class='news-meta'>
                <span class='news-source'>{source}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

elif app_mode == "📊 Stock Dashboard":
    # Stock dashboard only
    if ticker_symbol:
        # Calculate dates
        end_date = datetime.now()
        if timeframe == "1M":
            start_date = end_date - timedelta(days=30)
        elif timeframe == "3M":
            start_date = end_date - timedelta(days=90)
        elif timeframe == "6M":
            start_date = end_date - timedelta(days=180)
        elif timeframe == "1Y":
            start_date = end_date - timedelta(days=365)
        elif timeframe == "5Y":
            start_date = end_date - timedelta(days=365*5)
        elif timeframe == "10Y":
            start_date = end_date - timedelta(days=365*10)
        else:
            start_date = end_date - timedelta(days=365*20)
        
        interval_map = {"Daily": "1d", "Weekly": "1wk", "Monthly": "1mo"}
        interval = interval_map[chart_interval]
        
        with st.spinner(f'🔄 Loading {ticker_symbol} data...'):
            ticker_data = yf.Ticker(ticker_symbol)
            df = ticker_data.history(start=start_date, end=end_date, interval=interval)
            
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            
            try:
                info = ticker_data.info
                company_name = info.get('longName', ticker_symbol)
                market_cap = info.get('marketCap', 0)
                current_price = df['Close'].iloc[-1] if not df.empty else 0
                prev_close = info.get('previousClose', 0)
                pe_ratio = info.get('trailingPE', 'N/A')
            except:
                company_name = ticker_symbol
                market_cap = 0
                current_price = df['Close'].iloc[-1] if not df.empty else 0
                prev_close = df['Close'].iloc[0] if not df.empty else 0
                pe_ratio = 'N/A'
            
            # Fetch earnings
            earnings_data = []
            try:
                earnings = ticker_data.get_earnings_dates(limit=100)
                if earnings is not None and len(earnings) > 0:
                    earnings.index = earnings.index.tz_localize(None)
                    for date, row in earnings.iterrows():
                        if pd.Timestamp(start_date) <= date <= pd.Timestamp(end_date):
                            earnings_data.append({
                                'date': date,
                                'eps_estimate': row.get('EPS Estimate', 'N/A'),
                                'eps_actual': row.get('Reported EPS', 'N/A'),
                                'surprise': row.get('Surprise(%)', 'N/A')
                            })
            except:
                pass
            
            if not df.empty:
                price_change = current_price - prev_close
                price_change_pct = (price_change / prev_close * 100) if prev_close else 0
                
                # Metrics
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    st.markdown(f"""
                    <div class='info-box'>
                        <div class='metric-label'>Company</div>
                        <div class='metric-value' style='font-size: 18px;'>{company_name[:20]}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    color_class = "positive" if price_change >= 0 else "negative"
                    st.markdown(f"""
                    <div class='info-box'>
                        <div class='metric-label'>Current Price</div>
                        <div class='metric-value'>${current_price:.2f}</div>
                        <div class='{color_class}' style='font-size: 14px; margin-top: 5px;'>
                            {'+' if price_change >= 0 else ''}{price_change:.2f} ({price_change_pct:+.2f}%)
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    market_cap_display = "N/A"
                    if market_cap > 0:
                        if market_cap >= 1e12:
                            market_cap_display = f"${market_cap/1e12:.2f}T"
                        elif market_cap >= 1e9:
                            market_cap_display = f"${market_cap/1e9:.2f}B"
                        else:
                            market_cap_display = f"${market_cap/1e6:.2f}M"
                    
                    st.markdown(f"""
                    <div class='info-box'>
                        <div class='metric-label'>Market Cap</div>
                        <div class='metric-value' style='font-size: 18px;'>{market_cap_display}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    st.markdown(f"""
                    <div class='info-box'>
                        <div class='metric-label'>P/E Ratio</div>
                        <div class='metric-value' style='font-size: 18px;'>{pe_ratio if isinstance(pe_ratio, str) else f'{pe_ratio:.2f}'}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col5:
                    earnings_badge = f"<span class='status-badge badge-success'>✓ {len(earnings_data)} Earnings</span>" if earnings_data else "<span class='status-badge'>⚠ No Data</span>"
                    st.markdown(f"""
                    <div class='info-box'>
                        <div class='metric-label'>Earnings Reports</div>
                        <div style='margin-top: 8px;'>{earnings_badge}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("---")
                
                # Create chart
                fig = make_subplots(
                    rows=2, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.03,
                    row_heights=[0.7, 0.3]
                )
                
                fig.add_trace(go.Candlestick(
                    x=df.index,
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'],
                    name="Price",
                    increasing_line_color='#00ff00',
                    decreasing_line_color='#ff0000'
                ), row=1, col=1)
                
                if earnings_data:
                    for earning in earnings_data:
                        date = earning['date']
                        closest_date = df.index[df.index.get_indexer([date], method='nearest')[0]]
                        y_position = df.loc[closest_date]['Low'] * 0.96
                        
                        hover_text = f"<b>📊 EARNINGS</b><br>Date: {date.strftime('%Y-%m-%d')}<br>"
                        hover_text += f"EPS Est: {earning['eps_estimate']}<br>EPS Actual: {earning['eps_actual']}"
                        
                        fig.add_trace(go.Scatter(
                            x=[closest_date],
                            y=[y_position],
                            mode='markers+text',
                            marker=dict(size=32, color='#00D9FF', symbol='square'),
                            text='Q',
                            textfont=dict(color='#ffffff', size=14),
                            hovertext=hover_text,
                            hoverinfo='text',
                            showlegend=False
                        ), row=1, col=1)
                
                colors = ['#00ff00' if row['Close'] >= row['Open'] else '#ff0000' for _, row in df.iterrows()]
                fig.add_trace(go.Bar(
                    x=df.index,
                    y=df['Volume'],
                    marker_color=colors,
                    name="Volume",
                    opacity=0.7
                ), row=2, col=1)
                
                fig.update_layout(
                    template="plotly_dark",
                    height=800,
                    xaxis_rangeslider_visible=False,
                    showlegend=False,
                    paper_bgcolor='#1c1c1e',
                    plot_bgcolor='#2c2c2e',
                    margin=dict(l=50, r=50, t=30, b=30)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                if earnings_data:
                    st.markdown("### 📊 Earnings Calendar")
                    earnings_df = pd.DataFrame(earnings_data)
                    earnings_df['date'] = earnings_df['date'].dt.strftime('%Y-%m-%d')
                    earnings_df.columns = ['Date', 'EPS Estimate', 'EPS Actual', 'Surprise (%)']
                    st.dataframe(earnings_df, use_container_width=True, hide_index=True)
            else:
                st.error(f"❌ No data found for {ticker_symbol}")

else:  # Combined View
    col_news, col_stock = st.columns([1, 1])
    
    with col_news:
        st.markdown("## 📰 Top Stories")
        with st.spinner('Loading news...'):
            news_data = NewsAPI.fetch_news(news_api_key if news_api_key else None, news_category)
        
        for i, article in enumerate(news_data[:5]):
            title = article.get('title', 'No title')
            source = article.get('source', {}).get('name', 'Unknown') if isinstance(article.get('source'), dict) else article.get('source', 'Unknown')
            published = article.get('publishedAt', '')
            time_ago = format_time_ago(published)
            
            st.markdown(f"""
            <div class='news-card'>
                <div class='news-title' style='font-size: 16px;'>{title}</div>
                <div class='news-meta'>
                    <span class='news-source'>{source}</span>
                    <span>•</span>
                    <span>{time_ago}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with col_stock:
        st.markdown(f"## 📊 {ticker_symbol} Overview")
        
        if ticker_symbol:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365 if timeframe == "1Y" else 30)
            
            with st.spinner(f'Loading {ticker_symbol}...'):
                ticker_data = yf.Ticker(ticker_symbol)
                df = ticker_data.history(start=start_date, end=end_date, interval="1d")
                
                if not df.empty:
                    try:
                        info = ticker_data.info
                        current_price = df['Close'].iloc[-1]
                        prev_close = info.get('previousClose', df['Close'].iloc[0])
                        price_change = current_price - prev_close
                        price_change_pct = (price_change / prev_close * 100) if prev_close else 0
                        
                        color_class = "positive" if price_change >= 0 else "negative"
                        st.markdown(f"""
                        <div class='info-box' style='text-align: center;'>
                            <div class='metric-value' style='font-size: 36px;'>${current_price:.2f}</div>
                            <div class='{color_class}' style='font-size: 18px; margin-top: 10px;'>
                                {'+' if price_change >= 0 else ''}{price_change:.2f} ({price_change_pct:+.2f}%)
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Mini chart
                        fig = go.Figure(go.Scatter(
                            x=df.index,
                            y=df['Close'],
                            mode='lines',
                            line=dict(color='#00ff00' if price_change >= 0 else '#ff0000', width=2),
                            fill='tozeroy',
                            fillcolor='rgba(0, 255, 0, 0.1)' if price_change >= 0 else 'rgba(255, 0, 0, 0.1)'
                        ))
                        
                        fig.update_layout(
                            template="plotly_dark",
                            height=300,
                            showlegend=False,
                            paper_bgcolor='#1c1c1e',
                            plot_bgcolor='#2c2c2e',
                            margin=dict(l=10, r=10, t=10, b=10),
                            xaxis=dict(visible=False),
                            yaxis=dict(visible=False)
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    except:
                        st.error("Error loading stock data")
                else:
                    st.error(f"No data for {ticker_symbol}")