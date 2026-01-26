import streamlit as st
import finnhub
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests

# --- 1. CONFIGURATION & STYLING ---
FINNHUB_KEY = "d5rbglhr01qunvprr2mgd5rbglhr01qunvprr2n0"  # Get yours at https://finnhub.io/
finnhub_client = finnhub.Client(api_key=FINNHUB_KEY)

st.set_page_config(layout="wide", page_title="Python Analytics", page_icon="📈")

# Finviz/Dark Finance CSS
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stMetric { background-color: #1e222d; padding: 15px; border-radius: 5px; border: 1px solid #333; }
    .css-10trblm { color: #00ff00 !important; } /* Metric color */
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA FUNCTIONS ---
@st.cache_data(ttl=3600)
def get_historical_data(symbol):
    # Finnhub Stock Candles (Daily)
    end = int(datetime.now().timestamp())
    start = int((datetime.now() - timedelta(days=365)).timestamp())
    res = finnhub_client.stock_candles(symbol, 'D', start, end)
    
    if res['s'] == 'ok':
        df = pd.DataFrame(res)
        df['t'] = pd.to_datetime(df['t'], unit='s')
        return df
    return pd.DataFrame()

def get_company_stats(symbol):
    quote = finnhub_client.quote(symbol)
    metrics = finnhub_client.company_basic_financials(symbol, 'all')
    profile = finnhub_client.company_profile2(symbol=symbol)
    return quote, metrics, profile

# --- 3. MAIN INTERFACE ---
st.sidebar.title("🚀 Python Analytics")
ticker = st.sidebar.text_input("Search Ticker", value="TSLA").upper()

if ticker:
    try:
        quote, financials, profile = get_company_stats(ticker)
        candles = get_historical_data(ticker)

        # TOP ROW: Price & Market Info
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.title(f"{ticker} — {profile.get('name', 'Company Name')}")
            st.caption(f"{profile.get('finnhubIndustry', '')} • {profile.get('exchange', '')} • {profile.get('currency', '')}")
        
        with col2:
            st.metric("Price", f"${quote['c']}", f"{quote['d']:+.2f} ({quote['dp']:+.2f}%)")
        
        with col3:
            m_cap = financials['metric'].get('marketCapitalization', 0)
            st.metric("Market Cap", f"{m_cap:,.0f}M")

        # MAIN CHART: Historical Candlesticks
        if not candles.empty:
            fig = go.Figure(data=[go.Candlestick(
                x=candles['t'], open=candles['o'], high=candles['h'], low=candles['l'], close=candles['c'],
                name="Price", increasing_line_color='#089981', decreasing_line_color='#f23645'
            )])

            # SMA 20 & SMA 50 (Mimicking the image lines)
            candles['sma20'] = candles['c'].rolling(20).mean()
            candles['sma50'] = candles['c'].rolling(50).mean()
            fig.add_trace(go.Scatter(x=candles['t'], y=candles['sma20'], line=dict(color='#9c27b0', width=1), name='SMA 20'))
            fig.add_trace(go.Scatter(x=candles['t'], y=candles['sma50'], line=dict(color='#2196f3', width=1), name='SMA 50'))

            fig.update_layout(
                template="plotly_dark", height=500, xaxis_rangeslider_visible=False,
                margin=dict(l=0, r=0, t=20, b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True)

        # FUNDAMENTAL GRID: 12 Metrics
        st.subheader("Fundamentals")
        m = financials['metric']
        grid_cols = st.columns(6)
        
        metrics_list = [
            ("P/E", m.get('peAnnual')), ("Forward P/E", m.get('forwardPE')), ("P/S", m.get('psTTM')),
            ("EPS (TTM)", m.get('epsTTM')), ("Div Yield", m.get('dividendYield5Y')), ("ROE", m.get('roeTTM')),
            ("52W High", m.get('52WeekHigh')), ("52W Low", m.get('52WeekLow')), ("Beta", m.get('beta')),
            ("Quick Ratio", m.get('quickRatioQuarterly')), ("Debt/Eq", m.get('totalDebt/totalEquityQuarterly')), ("Payout Ratio", m.get('payoutRatioTTM'))
        ]

        for idx, (label, val) in enumerate(metrics_list):
            with grid_cols[idx % 6]:
                st.write(f"**{label}**")
                st.code(f"{val if val else 'N/A'}")

        # REVENUE & NEWS
        st.divider()
        st.subheader("Company News Feed")
        news = finnhub_client.company_news(ticker, _from=(datetime.now() - timedelta(7)).strftime('%Y-%m-%d'), to=datetime.now().strftime('%Y-%m-%d'))
        
        for article in news[:10]:
            with st.container():
                n_col1, n_col2 = st.columns([1, 4])
                n_col1.image(article.get('image', 'https://via.placeholder.com/150'), width=150)
                n_col2.markdown(f"### [{article['headline']}]({article['url']})")
                n_col2.caption(f"{article['source']} • {datetime.fromtimestamp(article['datetime']).strftime('%Y-%m-%d')}")
                n_col2.write(article['summary'][:200] + "...")

    except Exception as e:
        st.error(f"Error: {e}. Check your API key or Ticker name.")