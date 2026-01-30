import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# --- Custom CSS for Finviz-like styling ---
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
    .stTextInput input, .stDateInput input {
        background-color: #3a3a3c !important;
        border: 1px solid #48484a !important;
        color: #ffffff !important;
        border-radius: 4px !important;
        font-size: 16px !important;
        font-weight: 500 !important;
    }
    
    .stTextInput input::placeholder {
        color: #8e8e93 !important;
    }
    
    /* Radio button labels */
    .stRadio label {
        color: #ffffff !important;
        font-size: 14px !important;
        font-weight: 500 !important;
    }
    
    /* Radio button text */
    .stRadio > div > label > div > p {
        color: #ffffff !important;
        font-size: 14px !important;
    }
    
    /* Sidebar headers */
    .css-10trblm {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    
    /* All text in sidebar */
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    
    /* Markdown text */
    [data-testid="stSidebar"] .stMarkdown {
        color: #ffffff !important;
    }
    
    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 700;
        color: #00ff00;
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
    
    /* Status badge */
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
    
    .badge-warning {
        background-color: rgba(255, 165, 0, 0.15);
        color: #ffa500;
        border: 1px solid rgba(255, 165, 0, 0.3);
    }
    
    /* Divider */
    hr {
        border: none;
        border-top: 1px solid #2a2a2a;
        margin: 30px 0;
    }
</style>
""", unsafe_allow_html=True)

# --- Page Config ---
st.set_page_config(page_title="Pro Stock Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- Header with gradient ---
st.markdown("""
<div style='padding: 20px 0; margin-bottom: 30px;'>
    <h1 style='margin: 0; font-size: 42px;'>📊 PRO STOCK DASHBOARD</h1>
    <p style='color: #888888; margin-top: 5px; font-size: 14px;'>Real-time market data with earnings analysis</p>
</div>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.markdown("<h3 style='color: #ffffff; margin-bottom: 20px;'>⚙️ Configuration</h3>", unsafe_allow_html=True)
    ticker_symbol = st.text_input("🔍 Ticker Symbol", value="AAPL", help="Enter stock ticker (e.g., AAPL, TSLA, MSFT)", label_visibility="visible").upper()
    
    st.markdown("<hr style='border-color: #48484a; margin: 20px 0;'>", unsafe_allow_html=True)
    
    st.markdown("<p style='color: #ffffff; font-weight: 600; margin-bottom: 10px;'>📈 Timeframe</p>", unsafe_allow_html=True)
    timeframe = st.radio("Timeframe", ["1M", "3M", "6M", "1Y", "5Y", "10Y", "Max"], index=3, horizontal=True, label_visibility="collapsed")
    
    st.markdown("<hr style='border-color: #48484a; margin: 20px 0;'>", unsafe_allow_html=True)
    
    st.markdown("<p style='color: #ffffff; font-weight: 600; margin-bottom: 10px;'>📊 Chart Interval</p>", unsafe_allow_html=True)
    chart_interval = st.radio("Chart Interval", ["Daily", "Weekly", "Monthly"], index=0, horizontal=True, label_visibility="collapsed")
    
    # Calculate dates based on timeframe
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
    else:  # Max
        start_date = end_date - timedelta(days=365*20)  # 20 years max
    
    # Map chart interval to yfinance interval parameter
    interval_map = {
        "Daily": "1d",
        "Weekly": "1wk",
        "Monthly": "1mo"
    }
    interval = interval_map[chart_interval]

if ticker_symbol:
    with st.spinner(f'🔄 Loading {ticker_symbol} data...'):
        ticker_data = yf.Ticker(ticker_symbol)
        
        # Fetch Price Data with interval
        df = ticker_data.history(start=start_date, end=end_date, interval=interval)
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        
        # Fetch company info
        try:
            info = ticker_data.info
            company_name = info.get('longName', ticker_symbol)
            market_cap = info.get('marketCap', 0)
            current_price = df['Close'].iloc[-1] if not df.empty else 0
            prev_close = info.get('previousClose', 0)
            pe_ratio = info.get('trailingPE', 'N/A')
            dividend_yield = info.get('dividendYield', 0)
        except:
            company_name = ticker_symbol
            market_cap = 0
            current_price = df['Close'].iloc[-1] if not df.empty else 0
            prev_close = df['Close'].iloc[0] if not df.empty else 0
            pe_ratio = 'N/A'
            dividend_yield = 0
        
        # Fetch Earnings
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
            # Calculate metrics
            price_change = current_price - prev_close
            price_change_pct = (price_change / prev_close * 100) if prev_close else 0
            
            # Top metrics row
            st.markdown("---")
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
                    elif market_cap >= 1e6:
                        market_cap_display = f"${market_cap/1e6:.2f}M"
                    else:
                        market_cap_display = f"${market_cap:,.0f}"
                
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
                earnings_badge = f"<span class='status-badge badge-success'>✓ {len(earnings_data)} Earnings</span>" if earnings_data else "<span class='status-badge badge-warning'>⚠ No Data</span>"
                st.markdown(f"""
                <div class='info-box'>
                    <div class='metric-label'>Earnings Reports</div>
                    <div style='margin-top: 8px;'>{earnings_badge}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Create the chart
            fig = make_subplots(
                rows=2, cols=1, 
                shared_xaxes=True,
                vertical_spacing=0.03, 
                row_heights=[0.7, 0.3],
                subplot_titles=('', '')
            )

            # Candlestick Chart
            fig.add_trace(go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name="Price",
                increasing_line_color='#00ff00',
                decreasing_line_color='#ff0000',
                increasing_fillcolor='#00ff00',
                decreasing_fillcolor='#ff0000'
            ), row=1, col=1)

            # Add Earnings Markers
            if earnings_data:
                for earning in earnings_data:
                    date = earning['date']
                    closest_date = df.index[df.index.get_indexer([date], method='nearest')[0]]
                    y_position = df.loc[closest_date]['Low'] * 0.96
                    
                    hover_text = f"<b>📊 EARNINGS REPORT</b><br>"
                    hover_text += f"Date: {date.strftime('%Y-%m-%d')}<br>"
                    hover_text += f"EPS Est: {earning['eps_estimate']}<br>"
                    hover_text += f"EPS Actual: {earning['eps_actual']}<br>"
                    hover_text += f"Surprise: {earning['surprise']}%"
                    
                    # Use a square marker with 'Q' to represent Quarterly earnings
                    fig.add_trace(go.Scatter(
                        x=[closest_date],
                        y=[y_position],
                        mode='markers+text',
                        marker=dict(
                            size=32,
                            color='#00D9FF',
                            symbol='square',
                            line=dict(color='#ffffff', width=2)
                        ),
                        text='Q',
                        textfont=dict(color='#ffffff', size=14, family='Arial Black'),
                        textposition='middle center',
                        hovertext=hover_text,
                        hoverinfo='text',
                        showlegend=False,
                        name=f'Earnings {date.strftime("%Y-%m-%d")}'
                    ), row=1, col=1)

            # Volume Chart
            colors = ['#00ff00' if row['Close'] >= row['Open'] else '#ff0000' for _, row in df.iterrows()]
            fig.add_trace(go.Bar(
                x=df.index,
                y=df['Volume'],
                marker_color=colors,
                name="Volume",
                opacity=0.7
            ), row=2, col=1)

            # Update layout
            fig.update_layout(
                template="plotly_dark",
                height=800,
                xaxis_rangeslider_visible=False,
                showlegend=False,
                paper_bgcolor='#1c1c1e',
                plot_bgcolor='#2c2c2e',
                font=dict(color='#ffffff', family='Arial'),
                margin=dict(l=50, r=50, t=30, b=30),
                hovermode='x unified'
            )
            
            fig.update_xaxes(
                gridcolor='#3a3a3c',
                showgrid=True,
                zeroline=False
            )
            
            fig.update_yaxes(
                gridcolor='#3a3a3c',
                showgrid=True,
                zeroline=False
            )

            st.plotly_chart(fig, use_container_width=True)
            
            # Earnings details table
            if earnings_data:
                st.markdown("### 📊 Earnings Calendar")
                
                earnings_df = pd.DataFrame(earnings_data)
                earnings_df['date'] = earnings_df['date'].dt.strftime('%Y-%m-%d')
                earnings_df.columns = ['Date', 'EPS Estimate', 'EPS Actual', 'Surprise (%)']
                
                st.dataframe(
                    earnings_df,
                    use_container_width=True,
                    hide_index=True,
                    height=300
                )
            
        else:
            st.error(f"❌ No data found for ticker: {ticker_symbol}")
            st.info("💡 Try a different ticker symbol (e.g., AAPL, MSFT, GOOGL, TSLA)")