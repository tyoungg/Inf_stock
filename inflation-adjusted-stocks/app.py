import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
import time
from update_cpi import update_cpi
import datetime

# ---
# CONFIG
# ---

st.set_page_config(layout="wide", page_title="Inflation Adjusted Stocks")

st.title("Inflation Adjusted Stock Analysis")

# ---
# DATA MANAGEMENT (SIDEBAR)
# ---

st.sidebar.header("Data Management")

current_dir = os.path.dirname(os.path.abspath(__file__))
cpi_path = os.path.join(current_dir, "inflation_data/cpi.csv")

# Function to check for updates
def check_for_updates():
    if not os.path.exists(cpi_path):
        return True

    last_modified = os.path.getmtime(cpi_path)
    if (time.time() - last_modified) > 86400: # 24 hours
        return True
    return False

# Display Data Status
if os.path.exists(cpi_path):
    cpi_df = pd.read_csv(cpi_path)
    latest_cpi_date = pd.to_datetime(cpi_df['Date']).max().strftime('%Y-%m')
    st.sidebar.info(f"Latest CPI Month: {latest_cpi_date}")

    last_update = datetime.datetime.fromtimestamp(os.path.getmtime(cpi_path))
    st.sidebar.text(f"Last sync: {last_update.strftime('%Y-%m-%d %H:%M')}")

# Manual Refresh Button
if st.sidebar.button("Refresh Inflation Data"):
    with st.sidebar:
        with st.spinner("Updating CPI from FRED..."):
            success, msg = update_cpi()
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

st.sidebar.divider()
st.sidebar.header("Chart Settings")
chart_type = st.sidebar.selectbox("Chart Type", ["Line", "Candlestick"])
show_ohlc = st.sidebar.checkbox("Show Real OHLC", value=True) if chart_type == "Candlestick" else False

ticker = st.sidebar.text_input("Stock Symbol", "MSFT")

# ---
# AUTOMATED UPDATE (NON-BLOCKING)
# ---

if os.path.exists(cpi_path) and check_for_updates():
    with st.sidebar:
        with st.status("Checking for inflation updates...", expanded=False) as status:
            try:
                success, msg = update_cpi()
                if success:
                    status.update(label=f"Update successful: {msg}", state="complete")
                else:
                    status.update(label=f"Update failed: {msg}", state="error")
            except Exception as e:
                status.update(label=f"Update error: {str(e)}", state="error")

# ---
# LOAD STOCK DATA
# ---

with st.spinner(f"Loading data for {ticker}..."):
    # Note: latest yfinance versions use multi-level columns by default
    # We'll flatten them manually to ensure compatibility
    stock = yf.download(
        ticker,
        start="2015-01-01",
        auto_adjust=True
    )

if stock.empty:
    st.error(f"Invalid ticker or no data found for {ticker}.")
    st.stop()

# Flatten MultiIndex columns if present
if isinstance(stock.columns, pd.MultiIndex):
    stock.columns = stock.columns.get_level_values(0)

# ---
# LOAD CPI
# ---

cpi = pd.read_csv(cpi_path)
cpi["Date"] = pd.to_datetime(cpi["Date"])
cpi = cpi.set_index("Date")

# ---
# RESAMPLE MONTHLY
# ---

# Normalize column names to title case
stock.columns = [c.title() for c in stock.columns]

# Resample OHLC correctly
resampled = stock.resample("MS").agg({
    'Open': 'first',
    'High': 'max',
    'Low': 'min',
    'Close': 'last',
    'Volume': 'sum'
})

df = pd.DataFrame(resampled)

df = df.merge(cpi, left_index=True,
              right_index=True,
              how="left")

# Forward fill CPI in case stock data is newer than latest CPI report
df["CPI"] = df["CPI"].ffill()

# Drop rows where CPI is still NaN (before our first CPI data point)
df = df.dropna(subset=["CPI"])

# ---
# CALCULATIONS
# ---

df["Price"] = df["Close"]

df["Nominal_Return"] = (
    df["Price"].pct_change()
)

df["Inflation_Rate"] = (
    df["CPI"].pct_change()
)

df["Real_Return"] = (
    (1 + df["Nominal_Return"]) /
    (1 + df["Inflation_Rate"])
) - 1

base_cpi = df["CPI"].iloc[0]

# Real prices for all OHLC components
for col in ["Open", "High", "Low", "Close"]:
    df[f"Real_{col}"] = (
        df[col] * (base_cpi / df["CPI"])
    )

df["Real_Price"] = df["Real_Close"]

df["Inflation_Dependence"] = (
    df["Inflation_Rate"] /
    df["Nominal_Return"]
)

# ---
# CHART 1: Main Price Chart
# ---

fig1 = go.Figure()

if chart_type == "Line":
    fig1.add_trace(
        go.Scatter(
            x=df.index,
            y=df["Price"],
            name="Nominal Price"
        )
    )
    fig1.add_trace(
        go.Scatter(
            x=df.index,
            y=df["Real_Price"],
            name="Inflation Adjusted Price"
        )
    )
else:
    # Candlestick
    fig1.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Nominal OHLC",
            visible="legendonly" if show_ohlc else True
        )
    )

    if show_ohlc:
        fig1.add_trace(
            go.Candlestick(
                x=df.index,
                open=df["Real_Open"],
                high=df["Real_High"],
                low=df["Real_Low"],
                close=df["Real_Close"],
                name="Real OHLC"
            )
        )
    else:
         fig1.add_trace(
            go.Scatter(
                x=df.index,
                y=df["Real_Price"],
                name="Real Price (Line)",
                line=dict(color='cyan', width=2)
            )
        )

fig1.update_layout(
    title=f"{ticker} Nominal vs Real Price ({chart_type})",
    xaxis_rangeslider_visible=False,
    height=600
)

st.plotly_chart(fig1, use_container_width=True)

# ---
# CHART 2: Returns
# ---

fig2 = go.Figure()

fig2.add_trace(
    go.Scatter(
        x=df.index,
        y=df["Nominal_Return"] * 100,
        name="Nominal Return %"
    )
)

fig2.add_trace(
    go.Scatter(
        x=df.index,
        y=df["Real_Return"] * 100,
        name="Real Return %"
    )
)

fig2.update_layout(
    title=f"{ticker} Real vs Nominal Returns"
)

st.plotly_chart(fig2, use_container_width=True)

# ---
# CHART 3: Inflation Dependence
# ---

fig3 = go.Figure()

fig3.add_trace(
    go.Bar(
        x=df.index,
        y=df["Inflation_Dependence"],
        name="Inflation Dependence"
    )
)

fig3.update_layout(
    title=f"{ticker} Inflation Dependence Ratio"
)

st.plotly_chart(fig3, use_container_width=True)

# ---
# SUMMARY
# ---

latest = df.iloc[-1]

col1, col2, col3 = st.columns(3)

col1.metric(
    "Nominal Return",
    f"{latest['Nominal_Return']:.2%}"
)

col2.metric(
    "Inflation Rate",
    f"{latest['Inflation_Rate']:.2%}"
)

col3.metric(
    "Real Return",
    f"{latest['Real_Return']:.2%}"
)

st.dataframe(df)
