import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.title("Financial Dashboard")

# 1. Sidebar for Ticker Input
ticker_symbol = st.sidebar.text_input("Enter Ticker", value="AAPL").upper()

# 2. Fetch Data using yfinance
if ticker_symbol:
    ticker_data = yf.Ticker(ticker_symbol)
    
    # Get company info (Replaces company_profile2)
    info = ticker_data.info
    st.header(info.get('longName', ticker_symbol))
    st.write(info.get('longBusinessSummary', "No description available."))

    # 3. Get Historical Data (Replaces stock_candles)
    # period options: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    df = ticker_data.history(period="1y")

    if not df.empty:
        # 4. Create Candlestick Chart
        fig = go.Figure(data=[go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close']
        )])
        
        fig.update_layout(title=f"{ticker_symbol} Price History", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig)
    else:
        st.error("Could not find data for that ticker. Please try a US symbol like AAPL or TSLA.")