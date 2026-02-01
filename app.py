import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from google import genai
from google.genai import types
from google.api_core import exceptions
import time
from datetime import datetime, timedelta

# --- 1. CONFIGURATION ---
GEMINI_API_KEY = "YOUR_API_KEY_HERE" # 🔑 Replace with your actual key
client = genai.Client(api_key=GEMINI_API_KEY)

# --- 2. THEME & CSS ---
st.set_page_config(page_title="AI Pro Dashboard", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: #1c1c1e; }
    [data-testid="stSidebar"] { background-color: #2c2c2e; border-right: 1px solid #3a3a3c; }
    .report-card { 
        background: #2c2c2e; padding: 20px; border-radius: 12px; 
        border-left: 6px solid #00D9FF; margin: 15px 0; color: white;
    }
    .info-box {
        background: #2c2c2e; padding: 15px; border-radius: 8px;
        border: 1px solid #48484a; margin: 5px 0;
    }
    .metric-label { color: #8e8e93; font-size: 12px; text-transform: uppercase; font-weight: 600; }
    .metric-value { color: #ffffff; font-size: 20px; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# --- 3. ROBUST DATA FETCHING ---
@st.cache_data(ttl=3600)
def get_historical_df(ticker, years):
    end = datetime.now()
    start = end - timedelta(days=365 * years)
    
    # Download data
    df = yf.download(ticker, start=start, end=end, auto_adjust=True)
    
    if df.empty:
        return df

    # CRITICAL FIX: Flatten MultiIndex columns
    # This turns ('NVDA', 'Close') into just 'Close'
    if isinstance(df.columns, pd.MultiIndex):
        # We take the level that contains OHLCV (usually level 0 or 1 depending on version)
        if ticker in df.columns.levels[0]:
            df.columns = df.columns.get_level_values(1)
        else:
            df.columns = df.columns.get_level_values(0)
    
    return df

def get_safe_ticker_data(ticker_str):
    t = yf.Ticker(ticker_str)
    info_data = {}
    earnings_data = None
    try:
        raw_info = t.info
        if isinstance(raw_info, dict): info_data = raw_info
    except: 
        info_data = {"longName": ticker_str}
    try:
        earnings_data = t.get_earnings_dates(limit=16)
        if earnings_data is not None: 
            earnings_data.index = earnings_data.index.tz_localize(None)
    except: 
        pass
    return info_data, earnings_data

# --- 4. AI RESEARCH ---
def gemini_research(ticker, date_obj, pct):
    date_s = date_obj.strftime('%Y-%m-%d')
    prompt = f"Research {ticker} news for {date_s}. Price moved {pct:.2f}%. Explain why."
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash", contents=prompt,
            config=types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())])
        )
        return response.text
    except: return "AI Research currently unavailable."

# --- 5. SIDEBAR & LOGIC ---
with st.sidebar:
    st.title("⚙️ Controls")
    ticker_sym = st.text_input("Ticker Symbol", value="NVDA").upper()
    years_val = st.slider("History (Years)", 1, 5, 2)
    vol_trigger = st.slider("Volatility Trigger (%)", 1.0, 15.0, 4.0)
    deep_dive = st.button("🔍 Run AI Deep Dive", type="primary", use_container_width=True)

if ticker_sym:
    df = get_historical_df(ticker_sym, years_val)
    info, earnings_df = get_safe_ticker_data(ticker_sym)

    if not df.empty:
        # Detect Volatility - Now works because 'Close' is a simple column
        df['Change'] = df['Close'].pct_change() * 100
        vol_events = df[abs(df['Change']) >= vol_trigger].copy()

        # Header Metrics
        st.subheader(f"{info.get('longName', ticker_sym)}")
        m1, m2, m3 = st.columns(3)
        
        # Ensure values are simple floats for formatting
        latest_price = float(df['Close'].iloc[-1])
        market_cap = info.get('marketCap', 0)
        
        m1.markdown(f"<div class='info-box'><p class='metric-label'>Price</p><p class='metric-value'>${latest_price:.2f}</p></div>", unsafe_allow_html=True)
        m2.markdown(f"<div class='info-box'><p class='metric-label'>Market Cap</p><p class='metric-value'>${market_cap/1e12:.2f}T</p></div>", unsafe_allow_html=True)
        m3.markdown(f"<div class='info-box'><p class='metric-label'>Volatility Events</p><p class='metric-value'>{len(vol_events)} ⚡</p></div>", unsafe_allow_html=True)

        # --- 6. CHARTING ---
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
        
        # Main Candlestick
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], 
            low=df['Low'], close=df['Close'], name="Price"
        ), row=1, col=1)

        # ⚡ Volatility Markers
        if not vol_events.empty:
            fig.add_trace(go.Scatter(
                x=vol_events.index, y=vol_events['High'] * 1.05, 
                mode='markers+text', text='⚡', name='Volatility', 
                hovertext=[f"Move: {p:.2f}%" for p in vol_events['Change']]
            ), row=1, col=1)

        # Q Earnings Markers
        if earnings_df is not None:
            mask = (earnings_df.index >= df.index.min()) & (earnings_df.index <= df.index.max())
            e_dates = earnings_df[mask].index.intersection(df.index)
            if not e_dates.empty:
                fig.add_trace(go.Scatter(
                    x=e_dates, y=df.loc[e_dates]['Low'] * 0.95, 
                    mode='markers+text', text='Q', name='Earnings', 
                    marker=dict(size=12, color='#00D9FF', symbol='square')
                ), row=1, col=1)

        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color='#48484a', opacity=0.4), row=2, col=1)
        fig.update_layout(template="plotly_dark", height=600, showlegend=False, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

        # --- 7. AI DEEP DIVE ---
        if deep_dive:
            st.header("🤖 AI Event Analysis")
            top_swings = vol_events.sort_values(by='Change', key=abs, ascending=False).head(5)
            for date, row in top_swings.iterrows():
                with st.spinner(f"Analyzing {date.date()}..."):
                    insight = gemini_research(ticker_sym, date, row['Change'])
                    st.markdown(f"<div class='report-card'><h4>📅 {date.strftime('%Y-%m-%d')} | {row['Change']:+.2f}%</h4><p>{insight}</p></div>", unsafe_allow_html=True)
            st.balloons()
    else:
        st.error(f"No data found for {ticker_sym}. Please check the ticker symbol.")