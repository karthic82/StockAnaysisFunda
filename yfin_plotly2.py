import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime, timedelta

# 1. Setup the Streamlit page layout
st.set_page_config(page_title="Stock Analysis", layout="wide")
st.title("📈 Interactive Stock Analysis Dashboard")

# 2. Create a sidebar for user inputs
st.sidebar.header("Search Parameters")
ticker_symbol = st.sidebar.text_input("Enter Ticker Symbol (e.g., AAPL, MSFT, TSLA)", "AAPL").upper()

# Default date range: 1 year ago to today
default_start = datetime.today() - timedelta(days=365)
start_date = st.sidebar.date_input("Start Date", default_start)
end_date = st.sidebar.date_input("End Date", datetime.today())

# 3. Fetch the data using yfinance
@st.cache_data # This tells Streamlit to cache the data so it doesn't re-download on every click
def load_data(ticker, start, end):
    stock = yf.Ticker(ticker)
    df = stock.history(start=start, end=end)
    df.reset_index(inplace=True)
    # Convert timezone-aware dates to timezone-naive so Streamlit/Plotly handles them easily
    if 'Date' in df.columns and pd.api.types.is_datetime64_any_dtype(df['Date']):
        df['Date'] = df['Date'].dt.tz_localize(None)
    return df

data = load_data(ticker_symbol, start_date, end_date)

# 4. Display the Chart and Data
if not data.empty:
    st.subheader(f"Price History for {ticker_symbol}")
    
    # Create the Plotly Candlestick chart
    fig = go.Figure(data=[go.Candlestick(
        x=data['Date'],
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name=ticker_symbol
    )])
    
    # Format the chart layout
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        xaxis_rangeslider_visible=False,
        template="plotly_white"
    )
    
    # Render the Plotly chart in Streamlit
    st.plotly_chart(fig, use_container_width=True)
    
    # Show the raw data table below the chart
    st.subheader("Raw Data")
    st.dataframe(data.sort_values(by="Date", ascending=False).head(10))

else:
    st.error(f"No data found for {ticker_symbol}. Please check the ticker symbol or date range.")