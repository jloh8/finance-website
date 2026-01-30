import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# --- Page Config ---
st.set_page_config(page_title="Financial Dashboard", layout="wide")

st.title("📈 Stock Market Dashboard")

# --- Sidebar Inputs ---
st.sidebar.header("User Input")
ticker_symbol = st.sidebar.text_input("Enter Ticker", value="AAPL").upper()

start_date = st.sidebar.date_input("Start Date", value=datetime.now() - timedelta(days=365))
end_date = st.sidebar.date_input("End Date", value=datetime.now())

# --- Data Fetching ---
if ticker_symbol:
    with st.spinner(f'Fetching {ticker_symbol}...'):
        ticker_data = yf.Ticker(ticker_symbol)
        
        # 1. Fetch Info safely
        try:
            info = ticker_data.info
            if info and 'longName' in info:
                st.header(info.get('longName'))
                st.write(info.get('longBusinessSummary', ''))
        except:
            pass

        # 2. Fetch Historical Data
        df = ticker_data.history(start=start_date, end=end_date)

        if not df.empty:
            # Metrics
            col1, col2, col3 = st.columns(3)
            current_price = df['Close'].iloc[-1]
            price_change = current_price - df['Close'].iloc[-2]
            
            col1.metric("Current Price", f"${current_price:,.2f}", f"{price_change:,.2f}")
            col2.metric("High (Period)", f"${df['High'].max():,.2f}")
            col3.metric("Volume (Today)", f"{df['Volume'].iloc[-1]:,}")

            # 3. Create Subplots (Row 1: Price, Row 2: Volume)
            # row_heights specifies that the price chart takes 70% and volume 30%
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                               vertical_spacing=0.03, row_heights=[0.7, 0.3])

            # Add Candlestick to Row 1
            fig.add_trace(go.Candlestick(
                x=df.index,
                open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'],
                name="Price"
            ), row=1, col=1)

            # Add Volume Bar Chart to Row 2
            # We color the bars based on whether the day was "Up" or "Down"
            colors = ['green' if row['Close'] >= row['Open'] else 'red' for _, row in df.iterrows()]
            
            fig.add_trace(go.Bar(
                x=df.index,
                y=df['Volume'],
                marker_color=colors,
                name="Volume"
            ), row=2, col=1)

            # Layout tweaks
            fig.update_layout(
                title=f"{ticker_symbol} Technical View",
                yaxis_title="Price (USD)",
                yaxis2_title="Volume",
                xaxis_rangeslider_visible=False, # Hide slider for cleaner look
                template="plotly_dark",
                height=700,
                showlegend=False
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("No data found. Please check the ticker symbol.")