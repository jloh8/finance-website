import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# --- Page Config ---
st.set_page_config(page_title="Financial Dashboard", layout="wide")
st.title("📈 Stock Dashboard with Earnings")

# --- Sidebar Inputs ---
st.sidebar.header("User Input")
ticker_symbol = st.sidebar.text_input("Enter Ticker", value="AAPL").upper()
start_date = st.sidebar.date_input("Start Date", value=datetime.now() - timedelta(days=365))
end_date = st.sidebar.date_input("End Date", value=datetime.now())

if ticker_symbol:
    with st.spinner(f'Loading {ticker_symbol}...'):
        ticker_data = yf.Ticker(ticker_symbol)
        
        # 1. Fetch Price Data
        df = ticker_data.history(start=start_date, end=end_date)
        # Remove timezone from price data to match earnings data
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        
        # 2. Fetch ALL Earnings (broader date range to ensure we get them)
        earnings_data = []
        try:
            earnings = ticker_data.get_earnings_dates(limit=100)  # Get more dates
            if earnings is not None and len(earnings) > 0:
                # Remove timezone and filter
                earnings.index = earnings.index.tz_localize(None)
                
                for date, row in earnings.iterrows():
                    # Check if date falls within our chart range
                    if pd.Timestamp(start_date) <= date <= pd.Timestamp(end_date):
                        earnings_data.append({
                            'date': date,
                            'eps_estimate': row.get('EPS Estimate', 'N/A'),
                            'eps_actual': row.get('Reported EPS', 'N/A'),
                            'surprise': row.get('Surprise(%)', 'N/A')
                        })
                
                st.sidebar.success(f"✅ Found {len(earnings_data)} earnings dates")
            else:
                st.sidebar.warning("⚠️ No earnings data available")
        except Exception as e:
            st.sidebar.error(f"❌ Earnings error: {str(e)}")

        if not df.empty:
            # Create chart
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                               vertical_spacing=0.05, row_heights=[0.7, 0.3])

            # --- Candlestick Chart ---
            fig.add_trace(go.Candlestick(
                x=df.index, open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'], name="Price"
            ), row=1, col=1)

            # --- Add Earnings Markers ---
            if earnings_data:
                for earning in earnings_data:
                    date = earning['date']
                    
                    # Find the closest trading day
                    closest_date = df.index[df.index.get_indexer([date], method='nearest')[0]]
                    y_position = df.loc[closest_date]['Low'] * 0.97
                    
                    # Create hover text
                    hover_text = f"<b>EARNINGS</b><br>"
                    hover_text += f"Date: {date.strftime('%Y-%m-%d')}<br>"
                    hover_text += f"EPS Est: {earning['eps_estimate']}<br>"
                    hover_text += f"EPS Actual: {earning['eps_actual']}<br>"
                    hover_text += f"Surprise: {earning['surprise']}%"
                    
                    # Add marker
                    fig.add_trace(go.Scatter(
                        x=[closest_date],
                        y=[y_position],
                        mode='markers+text',
                        marker=dict(size=25, color='gold', symbol='star', 
                                   line=dict(color='black', width=2)),
                        text='E',
                        textfont=dict(color='black', size=14, family='Arial Black'),
                        textposition='middle center',
                        hovertext=hover_text,
                        hoverinfo='text',
                        showlegend=False,
                        name=f'Earnings {date.strftime("%Y-%m-%d")}'
                    ), row=1, col=1)

            # --- Volume Chart ---
            colors = ['green' if r['Close'] >= r['Open'] else 'red' for _, r in df.iterrows()]
            fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name="Volume"), 
                         row=2, col=1)

            fig.update_layout(
                template="plotly_dark", 
                height=800, 
                xaxis_rangeslider_visible=False,
                showlegend=False, 
                yaxis_title="Price (USD)", 
                yaxis2_title="Volume",
                hovermode='closest'
            )

            st.plotly_chart(fig, use_container_width=True)
            
            # Show earnings summary
            if earnings_data:
                st.subheader(f"📊 {len(earnings_data)} Earnings Reports in Chart")
                for earning in earnings_data:
                    cols = st.columns([2, 1, 1, 1])
                    with cols[0]:
                        st.write(f"**{earning['date'].strftime('%Y-%m-%d')}**")
                    with cols[1]:
                        st.write(f"Est: {earning['eps_estimate']}")
                    with cols[2]:
                        st.write(f"Act: {earning['eps_actual']}")
                    with cols[3]:
                        st.write(f"Surprise: {earning['surprise']}%")
        else:
            st.error("❌ No price data found for this ticker")