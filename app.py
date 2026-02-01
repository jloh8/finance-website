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
GEMINI_API_KEY = "AIzaSyB2yqLAFCq-cZIgPgY0Ewfg9__YX0mu_WY" # 🔑 Replace with your actual key
client = genai.Client(api_key=GEMINI_API_KEY)

# --- 2. THEME & CSS ---
st.set_page_config(page_title="AI Pro Dashboard", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: #1c1c1e; }
    [data-testid="stSidebar"] { background-color: #2c2c2e; border-right: 1px solid #3a3a3c; }
    .report-card { 
        background: #2c2c2e; padding: 20px; border-radius: 12px; 
        border-left: 6px solid #4285F4; margin: 15px 0; color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .info-box {
        background: #2c2c2e; padding: 15px; border-radius: 8px;
        border: 1px solid #48484a; margin: 5px 0;
    }
    .metric-label { color: #8e8e93; font-size: 12px; text-transform: uppercase; font-weight: 600; }
    .metric-value { color: #ffffff; font-size: 20px; font-weight: 700; }
    .move-pos { color: #0f9d58; font-weight: bold; }
    .move-neg { color: #d93025; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 3. ROBUST DATA FETCHING & FLATTENING ---
@st.cache_data(ttl=3600)
def get_swing_data(ticker, threshold, years):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * years)
    try:
        data = yf.download(ticker, start=start_date, end=end_date, auto_adjust=True)
        if data.empty: return None, []
        
        # FIX: Flatten MultiIndex columns if they exist
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(1) if 'Close' in data.columns.get_level_values(1) else data.columns.get_level_values(0)

        # Calculate daily change
        data['Change'] = data['Close'].pct_change() * 100
        swings = data[abs(data['Change']) >= threshold].sort_index(ascending=False)
        
        results = []
        for date, row in swings.iterrows():
            results.append({
                'date': date,
                'close': float(row['Close']),
                'pct': float(row['Change'])
            })
        return data, results
    except Exception as e:
        st.error(f"YFinance Error: {e}")
        return None, []

def get_safe_ticker_info(ticker_str):
    t = yf.Ticker(ticker_str)
    try:
        info = t.info
        earnings = t.get_earnings_dates(limit=16)
        if earnings is not None: earnings.index = earnings.index.tz_localize(None)
        return info, earnings
    except:
        return {"longName": ticker_str}, None

# --- 4. AI ANALYSIS FUNCTION (With Grounding & Retry) ---
def analyze_move_with_retry(ticker, date_obj, pct_change, max_retries=3):
    date_str = date_obj.strftime('%B %d, %Y')
    prompt = (f"Search Google News and financial reports for {ticker} on {date_str}. "
              f"The stock moved {pct_change:.2f}% on this day. "
              f"Explain the primary news catalysts or macro reasons for this move.")

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                )
            )
            return response.text
        except exceptions.ResourceExhausted:
            wait_time = (2 ** attempt) * 10
            time.sleep(wait_time)
        except Exception as e:
            return f"❌ AI Error: {str(e)}"
    return "⏭️ Max retries reached. API is busy."

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Parameters")
    ticker_input = st.text_input("Ticker Symbol", "TSLA").upper()
    swing_limit = st.slider("Volatility Trigger (%)", 1.0, 15.0, 5.0)
    lookback = st.number_input("Years to Analyze", 1, 5, 1)
    st.info("💡 Uses Google Search grounding for analysis.")

# --- 6. MAIN UI LOGIC ---
if ticker_input:
    full_df, swing_list = get_swing_data(ticker_input, swing_limit, lookback)
    info, earnings_df = get_safe_ticker_info(ticker_input)

    if full_df is not None:
        # Header Stats
        st.title(f"📈 {info.get('longName', ticker_input)}")
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.markdown(f"<div class='info-box'><p class='metric-label'>Current Price</p><p class='metric-value'>${float(full_df['Close'].iloc[-1]):.2f}</p></div>", unsafe_allow_html=True)
        col_m2.markdown(f"<div class='info-box'><p class='metric-label'>Events Found</p><p class='metric-value'>{len(swing_list)}</p></div>", unsafe_allow_html=True)
        col_m3.markdown(f"<div class='info-box'><p class='metric-label'>Market Cap</p><p class='metric-value'>${info.get('marketCap', 0)/1e9:.2f}B</p></div>", unsafe_allow_html=True)

        # --- 7. MAIN CHART ---
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
        
        # Candlestick
        fig.add_trace(go.Candlestick(
            x=full_df.index, open=full_df['Open'], high=full_df['High'],
            low=full_df['Low'], close=full_df['Close'], name="Price"
        ), row=1, col=1)

        # Volatility Markers (⚡)
        if swing_list:
            swing_dates = [s['date'] for s in swing_list]
            swing_prices = [s['close'] * 1.05 for s in swing_list]
            fig.add_trace(go.Scatter(
                x=swing_dates, y=swing_prices, mode='markers+text',
                text='⚡', name='Volatility', textfont=dict(size=14),
                hovertext=[f"Move: {s['pct']:.2f}%" for s in swing_list]
            ), row=1, col=1)

        # Earnings Markers (Q)
        if earnings_df is not None:
            mask = (earnings_df.index >= full_df.index.min()) & (earnings_df.index <= full_df.index.max())
            e_dates = earnings_df[mask].index.intersection(full_df.index)
            if not e_dates.empty:
                fig.add_trace(go.Scatter(
                    x=e_dates, y=full_df.loc[e_dates]['Low'] * 0.95,
                    mode='markers+text', text='Q', name='Earnings',
                    marker=dict(size=12, color='#00D9FF', symbol='square')
                ), row=1, col=1)

        fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        # --- 8. AI ANALYSIS DEEP DIVE ---
        if st.button("🚀 Run AI Deep Dive into Events", type="primary", use_container_width=True):
            analysis_queue = swing_list[:8] # Limit to top 8
            st.markdown("## 🕵️ AI Event Analysis")
            
            my_bar = st.progress(0, text="AI is researching news...")
            
            for i, s in enumerate(analysis_queue):
                percent_complete = (i + 1) / len(analysis_queue)
                my_bar.progress(percent_complete, text=f"Researching {s['date'].strftime('%Y-%m-%d')}...")

                st.markdown(f"### 📅 {s['date'].strftime('%B %d, %Y')}")
                c1, c2 = st.columns([1, 2])
                
                with c1:
                    st.metric("Price Move", f"${s['close']:.2f}", f"{s['pct']:+.2f}%")
                    # Mini Context Chart
                    c_start, c_end = s['date'] - timedelta(days=10), s['date'] + timedelta(days=10)
                    mini_df = full_df.loc[c_start:c_end]
                    mini_fig = go.Figure(data=[go.Candlestick(x=mini_df.index, open=mini_df['Open'], high=mini_df['High'], low=mini_df['Low'], close=mini_df['Close'])])
                    mini_fig.update_layout(height=200, margin=dict(l=0,r=0,b=0,t=0), template="plotly_dark", xaxis_rangeslider_visible=False)
                    st.plotly_chart(mini_fig, use_container_width=True, key=f"mini_{i}")

                with c2:
                    ai_insight = analyze_move_with_retry(ticker_input, s['date'], s['pct'])
                    st.markdown(f"<div class='report-card'><b>AI Insight:</b><br>{ai_insight}</div>", unsafe_allow_html=True)
                
                st.markdown("---")
                time.sleep(2) # Buffer for API

            my_bar.empty()
            st.balloons()