import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# --- Page Config ---
st.set_page_config(page_title="Financial Dashboard", layout="wide")
st.title("📈 Pro Stock Dashboard")

# --- Sidebar Inputs ---
st.sidebar.header("User Input")
ticker_symbol = st.sidebar.text_input("Enter Ticker", value="AAPL").upper()
start_date = st.sidebar.date_input("Start Date", value=datetime.now() - timedelta(days=365))
end_date = st.sidebar.date_input("End Date", value=datetime.now())

if ticker_symbol:
    with st.spinner(f'Analyzing {ticker_symbol}...'):
        ticker_data = yf.Ticker(ticker_symbol)
        
        # 1. Fetch Price Data
        df = ticker_data.history(start=start_date, end=end_date)
        
        # 2. Fetch News (with Search Fallback for 2026 reliability)
        news = []
        try:
            news = ticker_data.news
            if not news:
                search = yf.Search(ticker_symbol, max_results=10)
                news = search.news
        except:
            news = []

        # 3. Fetch Earnings
        try:
            earnings = ticker_data.get_earnings_dates()
            if earnings is not None:
                earnings.index = earnings.index.tz_localize(None)
                mask = (earnings.index >= pd.Timestamp(start_date)) & (earnings.index <= pd.Timestamp(end_date))
                filtered_earnings = earnings.loc[mask]
            else:
                filtered_earnings = pd.DataFrame()
        except:
            filtered_earnings = pd.DataFrame()

        if not df.empty:
            # Layout: Price (70%) and Volume (30%)
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                               vertical_spacing=0.05, row_heights=[0.7, 0.3])

            # --- Candlestick Chart ---
            fig.add_trace(go.Candlestick(
                x=df.index, open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'], name="Price"
            ), row=1, col=1)

            # --- Add News Icons (📰) ---
            for article in news:
                ts = article.get('providerPublishTime') or article.get('publishTime')
                if ts:
                    pub_date = datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                    if pub_date in df.index.strftime('%Y-%m-%d'):
                        y_pos = df.loc[pub_date]['High'].max()
                        fig.add_annotation(
                            x=pub_date, y=y_pos, text="📰", 
                            showarrow=True, arrowhead=1,
                            hovertext=f"<b>NEWS:</b> {article.get('title')}",
                            row=1, col=1
                        )

            # --- Add Earnings Icons (E) ---
            for date, row in filtered_earnings.iterrows():
                date_str = date.strftime('%Y-%m-%d')
                if date_str in df.index.strftime('%Y-%m-%d'):
                    y_pos = df.loc[date_str]['Low'].min() * 0.95
                    fig.add_annotation(
                        x=date_str, y=y_pos, text="<b>E</b>", 
                        font=dict(color="white"), bgcolor="royalblue",
                        bordercolor="white", showarrow=False,
                        hovertext=f"<b>EARNINGS</b><br>EPS Est: {row.get('EPS Estimate')}<br>Actual: {row.get('Reported EPS')}",
                        row=1, col=1
                    )

            # --- Volume Chart ---
            colors = ['green' if r['Close'] >= r['Open'] else 'red' for _, r in df.iterrows()]
            fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name="Volume"), row=2, col=1)

            fig.update_layout(template="plotly_dark", height=800, xaxis_rangeslider_visible=False,
                              showlegend=False, yaxis_title="Price (USD)", yaxis2_title="Volume")

            st.plotly_chart(fig, use_container_width=True)

            # --- News & Earnings Summaries Below Chart ---
            col_news, col_earn = st.columns(2)
            
            with col_news:
                st.subheader("Latest Headlines")
                for article in news:
                    with st.expander(article.get('title', 'News Item')):
                        st.write(f"[Read Article]({article.get('link')})")

            with col_earn:
                st.subheader("Earnings Data")
                if not filtered_earnings.empty:
                    st.dataframe(filtered_earnings[['EPS Estimate', 'Reported EPS', 'Surprise(%)']])
                else:
                    st.write("No earnings data for this period.")
        else:
            st.error("Ticker data not found.")