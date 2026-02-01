import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from google import genai
from google.genai import types
from google.api_core import exceptions
import time
from datetime import datetime, timedelta

# --- CONFIGURATION ---
GEMINI_API_KEY = "AIzaSyB2yqLAFCq-cZIgPgY0Ewfg9__YX0mu_WY" # 🔑 Replace with your actual key
client = genai.Client(api_key=GEMINI_API_KEY)

st.set_page_config(page_title="Gemini Volatility Analyst", layout="wide", page_icon="📈")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .report-card { background: #f9f9f9; padding: 20px; border-radius: 12px; border-left: 6px solid #4285F4; margin: 15px 0; }
    .move-pos { color: #0f9d58; font-weight: bold; }
    .move-neg { color: #d93025; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- AI ANALYSIS FUNCTION WITH RETRY LOGIC ---
def analyze_move_with_retry(ticker, date_obj, pct_change, max_retries=3):
    """
    Calls Gemini with Google Search grounding. 
    Implements exponential backoff for 429 Rate Limit errors.
    """
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
            wait_time = (2 ** attempt) * 10  # Wait 10s, 20s, 40s...
            st.warning(f"⚠️ Rate limit hit for {date_str}. Retrying in {wait_time}s...")
            time.sleep(wait_time)
            
        except Exception as e:
            return f"❌ AI Error: {str(e)}"
            
    return "⏭️ Max retries reached for this date. API is busy."

# --- DATA FETCHING ---
@st.cache_data(ttl=3600)
def get_swing_data(ticker, threshold, years):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * years)
    
    try:
        data = yf.download(ticker, start=start_date, end=end_date)
        if data.empty: return None, []
        
        # Calculate daily change
        data['Change'] = data['Close'].pct_change() * 100
        swings = data[abs(data['Change']) >= threshold].sort_index(ascending=False)
        
        results = []
        for date, row in swings.iterrows():
            results.append({
                'date': date,
                'close': float(row['Close'].iloc[0] if isinstance(row['Close'], pd.Series) else row['Close']),
                'pct': float(row['Change'].iloc[0] if isinstance(row['Change'], pd.Series) else row['Change'])
            })
        return data, results
    except Exception as e:
        st.error(f"YFinance Error: {e}")
        return None, []

# --- MAIN UI ---
st.title("🤖 Gemini AI Stock Analyst")
st.write("Detecting major price swings and researching the 'Why' using Google Search Grounding.")

with st.sidebar:
    st.header("Search Parameters")
    ticker_input = st.text_input("Ticker Symbol", "TSLA").upper()
    swing_limit = st.slider("Volatility Trigger (%)", 1.0, 15.0, 5.0)
    lookback = st.number_input("Years to Analyze", 1, 5, 1)
    st.info("💡 Free Gemini API keys have a limit of ~15 requests per minute. Analysis may pause to wait for quota reset.")

if st.button("Deep Dive into Volatility", type="primary", use_container_width=True):
    full_df, swing_list = get_swing_data(ticker_input, swing_limit, lookback)
    
    if swing_list:
        # Limit to top 8 moves to avoid completely exhausting daily quota
        analysis_queue = swing_list[:8] 
        st.success(f"Found {len(swing_list)} moves. Analyzing the top {len(analysis_queue)}.")
        
        # Initialize Progress Bar
        progress_text = "AI Researcher is looking up news..."
        my_bar = st.progress(0, text=progress_text)
        
        for i, s in enumerate(analysis_queue):
            # Update Progress
            percent_complete = (i + 1) / len(analysis_queue)
            my_bar.progress(percent_complete, text=f"Analyzing move from {s['date'].strftime('%Y-%m-%d')}...")

            # Display UI for this swing
            move_class = "move-pos" if s['pct'] > 0 else "move-neg"
            st.markdown(f"### 📅 {s['date'].strftime('%B %d, %Y')}")
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.metric("Closing Price", f"${s['close']:.2f}", f"{s['pct']:+.2f}%")
                
                # Context Chart
                c_start = s['date'] - timedelta(days=10)
                c_end = s['date'] + timedelta(days=10)
                chart_df = full_df.loc[c_start:c_end]
                
                fig = go.Figure(data=[go.Candlestick(
                    x=chart_df.index, open=chart_df['Open'], high=chart_df['High'],
                    low=chart_df['Low'], close=chart_df['Close']
                )])
                fig.add_vline(x=s['date'], line_dash="dash", line_color="orange")
                fig.update_layout(height=280, margin=dict(l=0,r=0,b=0,t=0), template="plotly_white", xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True, key=f"chart_{i}")

            with col2:
                # Call Gemini with grounding
                ai_analysis = analyze_move_with_retry(ticker_input, s['date'], s['pct'])
                st.markdown(f"<div class='report-card'><b>AI Insight:</b><br>{ai_analysis}</div>", unsafe_allow_html=True)
                
            st.markdown("---")
            
            # Small buffer to avoid hitting TPM (Tokens Per Minute) limit immediately
            time.sleep(2) 

        my_bar.empty()
        st.balloons()
    else:
        st.warning("No moves found for that ticker/threshold.")