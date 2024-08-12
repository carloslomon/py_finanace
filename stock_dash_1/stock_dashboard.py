import streamlit as st 
import pandas as pd
import plotly.express as px 
import plotly.graph_objects as go
import yfinance as yf 
from datetime import datetime, timedelta 
import pytz 
import ta
st.set_page_config(layout='wide')

# Function to fetch stock data based on ticker, period, and interval 
def fetch_stock_data(ticker, period, interval):
    end_date = datetime.now()
    # It can be more than 1wk, but we will change that design later
    if period == '1wk':
        start_date = end_date - timedelta(days=7)
        data = yf.download(ticker, start=start_date, end=end_date, interval=interval)
    else:
        data = yf.download(ticker, period=period, interval=interval)
    return data

# Function to process data and align it with the timezone
def process_data_time(data):
    if data.index.tzinfo is None:
        # Localize the index to UTC 
        data.index = data.index.tz_localize('UTC')
        # Convert the index to Costa Rica timezone
        data.index = data.index.tz_convert('America/Costa_Rica')
    data.reset_index(inplace=True)
    data.rename(columns={'Date': 'Datetime'}, inplace=True)
    return data 

# Function to calculate basic metrics of the stock
def calc_basic_metrics(data):
    last_close = data['Close'].iloc[-1]  # Locate last close 
    prev_close = data['Close'].iloc[0]
    change = last_close - prev_close
    prcnt_chng = 100 * change / prev_close
    high = data['High'].max()
    low = data['Low'].min()
    vol = data['Volume'].sum()
    return last_close, change, prcnt_chng, high, low, vol

# Function to add simple moving avg (SMA) and exp moving avg (EMA) indicators 
def add_sma_ema(data, window=20):
    str_sma = 'SMA ' + str(window)
    str_ema = 'EMA ' + str(window)
    data[str_sma] = ta.trend.sma_indicator(data['Close'], window=window)
    data[str_ema] = ta.trend.ema_indicator(data['Close'], window=window)
    return data

# Part 2: Creating the Dashboard layout

# Setup the page layout 
#st.set_page_config(layout='wide')

st.title('Real-Time Stock Dashboard')

# Sidebar parameters 
window_sma_ema = 20
st.sidebar.header('Stock Chart Parameters')
ticker = st.sidebar.text_input('Ticker', 'NVDA')
time_period = st.sidebar.selectbox('Time Period', ['1d', '1wk', '1mo', '1y', 'max'])
window_sma_ema = st.sidebar.slider('Amount of Days for EMA and SMA', min_value=1, max_value=364, value=20, step=1)
chart_type = st.sidebar.selectbox('Chart Type', ['Candlestick', 'Line'])

# Global SMA and EMA names 
sma_name = 'SMA ' + str(window_sma_ema)
ema_name = 'EMA ' + str(window_sma_ema)
indicators = st.sidebar.multiselect('Technical Indicators', [sma_name, ema_name])

# Mapping of time periods to data intervals 
interval_mapping = {
    '1d': '1m',
    '1wk': '30m',
    '1mo': '1d',
    '1y': '1wk',
    'max': '1wk'
}

# Main content area development

if st.sidebar.button('Update'):
    data = fetch_stock_data(ticker, time_period, interval_mapping[time_period])
    data = process_data_time(data)
    data = add_sma_ema(data, window_sma_ema)

    last_close, change, prcnt_chng, high, low, vol = calc_basic_metrics(data)

    # Display main metrics 
    st.metric(label=f"{ticker} Last Price", value=f"{last_close:.2f} USD", delta=f"{change:.2f} ({prcnt_chng:.2f}%)")
    col1, col2, col3 = st.columns(3)
    col1.metric("High", f"{high:.2f} USD")
    col2.metric("Low", f"{low:.2f} USD")
    col3.metric("Volume", f"{vol:,}")

    # Plot the stock price chart 
    fig = go.Figure()
    if chart_type == 'Candlestick':
        fig.add_trace(go.Candlestick(x=data['Datetime'], 
                                     open=data['Open'],
                                     high=data['High'],
                                     low=data['Low'],
                                     close=data['Close']))
    else:
        fig = px.line(data, x='Datetime', y='Close') 
    
    # Add selected technical indicators 
    for indicator in indicators:
        if indicator == sma_name:
            fig.add_trace(go.Scatter(x=data['Datetime'], y=data[sma_name], name=sma_name))
        elif indicator == ema_name:
            fig.add_trace(go.Scatter(x=data['Datetime'], y=data[ema_name], name=ema_name))
    
    # Graph text formatting 
    fig.update_layout(title=f"{ticker} {time_period.upper()} Chart", 
                      xaxis_title='Time',
                      yaxis_title='Price (USD)',
                      height=750)
    st.plotly_chart(fig, use_container_width=True)

    # Display historical data and technical indicators 
    st.subheader('Historical Data')
    st.dataframe(data[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']])

    st.subheader('Technical Indicators')
    st.dataframe(data[['Datetime', sma_name, ema_name]])

    # Sidebar real-time prices 
    st.sidebar.header('Real-Time Stock Prices')
    stock_symbols = ['AAPL', 'AMZN', 'GOOGL', 'MSFT', 'NVDA']
    for sym in stock_symbols:
        real_time_data = fetch_stock_data(sym, '1d', '1m')
        if not real_time_data.empty:
            real_time_data = process_data_time(real_time_data)
            last_price = real_time_data['Close'].iloc[-1]
            change = last_price - real_time_data['Open'].iloc[0]
            prcnt_chng = 100 * change / real_time_data['Open'].iloc[0]
            st.sidebar.metric(f"{sym}", f"{last_price:.2f} USD", f"{change:.2f} ({prcnt_chng:.2f}%)")
    
    # Information section 
    st.sidebar.subheader('About the Stock Dashboard')
    st.sidebar.info('This dashboard was created by Carlos Alberto Lopez Montealegre. It provides stock data and simple technical indicators for various time periods. Use the sidebar to acquire information about the stock you want to study.')
















