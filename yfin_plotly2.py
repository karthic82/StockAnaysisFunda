import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime

# 1. Setup the Streamlit page layout (Light theme requested via image)
st.set_page_config(page_title="Stock Data Analysis", layout="wide")

# Center the main title like the reference image
st.markdown("<h1 style='text-align: center;'>Stock Data Analysis</h1>", unsafe_allow_html=True)

# 2. Recreate the top search bar layout
col1, col2, col3 = st.columns([2, 2, 6])
with col1:
    ticker_symbol = st.text_input("", "MSFT", label_visibility="collapsed").upper()
with col2:
    fetch_button = st.button("FETCH DATA")

# 3. Fetch data (fetching 2 years to ensure we have enough historical data for the 200 DMA)
@st.cache_data
def load_data(ticker):
    stock = yf.Ticker(ticker)
    # Fetch 2 years of history for moving averages and 1-year return math
    df = stock.history(period="2y")
    info = stock.info
    return df, info

if ticker_symbol:
    df, info = load_data(ticker_symbol)

    if not df.empty:
        # --- CALCULATIONS ---
        
        # Calculate Moving Averages
        df['20 DMA'] = df['Close'].rolling(window=20).mean()
        df['50 DMA'] = df['Close'].rolling(window=50).mean()
        df['100 DMA'] = df['Close'].rolling(window=100).mean()
        df['200 DMA'] = df['Close'].rolling(window=200).mean()

        # Calculate Returns (Approximate trading days)
        current_price = df['Close'].iloc[-1]
        
        def get_return(trading_days_ago):
            if len(df) > trading_days_ago:
                past_price = df['Close'].iloc[-(trading_days_ago + 1)]
                return ((current_price - past_price) / past_price) * 100
            return None

        ret_1w = get_return(5)     # ~5 trading days in a week
        ret_1m = get_return(21)    # ~21 trading days in a month
        ret_3m = get_return(63)    # ~63 trading days in 3 months
        ret_6m = get_return(126)   # ~126 trading days in 6 months
        ret_1y = get_return(252)   # ~252 trading days in a year

        # Get Financial Metrics
        high_52 = info.get('fiftyTwoWeekHigh', df['Close'].rolling(252).max().iloc[-1])
        low_52 = info.get('fiftyTwoWeekLow', df['Close'].rolling(252).min().iloc[-1])
        pe_ratio = info.get('trailingPE', 'N/A')
        beta = info.get('beta', 'N/A')

        pct_from_high = ((current_price - high_52) / high_52) * 100 if isinstance(high_52, (int, float)) else None
        pct_from_low = ((current_price - low_52) / low_52) * 100 if isinstance(low_52, (int, float)) else None

        # --- CHART RENDERING ---
        
        st.write(f"### {ticker_symbol} Historical Candlestick Chart")
        
        fig = go.Figure()
        
        # Add Candlestick
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Price'
        ))
        
        # Add Moving Averages
        fig.add_trace(go.Scatter(x=df.index, y=df['20 DMA'], line=dict(color='blue', width=1), name='20 DMA'))
        fig.add_trace(go.Scatter(x=df.index, y=df['50 DMA'], line=dict(color='magenta', width=1), name='50 DMA'))
        fig.add_trace(go.Scatter(x=df.index, y=df['100 DMA'], line=dict(color='orange', width=1), name='100 DMA'))
        fig.add_trace(go.Scatter(x=df.index, y=df['200 DMA'], line=dict(color='black', width=1), name='200 DMA'))
        
        # Format Chart Layout
        fig.update_layout(
            xaxis_rangeslider_visible=True,
            template="plotly_white",
            height=500,
            margin=dict(l=0, r=0, t=30, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)

        # --- METRICS TABLE RENDERING ---
        
        st.write("<br>", unsafe_allow_html=True)

        # Helper function to generate the colored HTML cells
        def format_metric(val, is_pct=True):
            if val is None or val == 'N/A':
                return "<td><div style='padding: 10px;'>N/A</div></td>"
            
            # Color logic based on the reference image
            if val < 0:
                bg_color, text_color = "red", "white"
            elif 0 <= val < 15:
                bg_color, text_color = "orange", "white"
            else:
                bg_color, text_color = "green", "white"
                
            display_val = f"{val:.2f}%" if is_pct else f"{val:.2f}"
            return f"<td><div style='background-color: {bg_color}; color: {text_color}; padding: 10px; font-weight: bold;'>{display_val}</div></td>"

        def format_plain(val):
            display_val = f"{val:.2f}" if isinstance(val, (int, float)) else str(val)
            return f"<td><div style='padding: 10px; color: black;'>{display_val}</div></td>"

        # Construct the HTML Table
        html_table = f"""
        <style>
            .metric-table {{ width: 100%; border-collapse: collapse; font-family: sans-serif; text-align: center; background-color: white; }}
            .metric-table th {{ font-size: 13px; font-weight: normal; color: #555; padding-bottom: 8px; border-bottom: 1px solid #ddd; }}
            .metric-table td {{ font-size: 14px; padding: 0; }}
        </style>
        <table class="metric-table">
            <tr>
                <th>1 Week Return</th>
                <th>1 Month Return</th>
                <th>3 Months Return</th>
                <th>6 Months Return</th>
                <th>1 Year Return</th>
                <th>52-Week High</th>
                <th>52-Week Low</th>
                <th>P/E Ratio</th>
                <th>Beta Value</th>
                <th>Percent(%) from High</th>
                <th>Percent(%) from Low</th>
            </tr>
            <tr>
                {format_metric(ret_1w)}
                {format_metric(ret_1m)}
                {format_metric(ret_3m)}
                {format_metric(ret_6m)}
                {format_metric(ret_1y)}
                {format_plain(high_52)}
                {format_plain(low_52)}
                {format_plain(pe_ratio)}
                {format_plain(beta)}
                {format_metric(pct_from_high)}
                {format_metric(pct_from_low)}
            </tr>
        </table>
        """
        
        st.markdown(html_table, unsafe_allow_html=True)

    else:
        st.error("No data found. Please check the ticker symbol.")