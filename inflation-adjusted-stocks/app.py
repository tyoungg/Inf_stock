import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

# ============================================
# CONFIG
# ============================================

st.set_page_config(layout="wide")

st.title("Inflation Adjusted Stock Analysis")

ticker = st.text_input("Stock Symbol", "MSFT")

# ============================================
# LOAD STOCK DATA
# ============================================

stock = yf.download(
    ticker,
    start="2015-01-01",
    auto_adjust=True
)

if stock.empty:
    st.error("Invalid ticker.")
    st.stop()

# ============================================
# LOAD CPI
# ============================================

# Use absolute path relative to this script
current_dir = os.path.dirname(os.path.abspath(__file__))
cpi_path = os.path.join(current_dir, "inflation_data/cpi.csv")
cpi = pd.read_csv(cpi_path)

cpi["Date"] = pd.to_datetime(cpi["Date"])
cpi = cpi.set_index("Date")

# ============================================
# RESAMPLE MONTHLY
# ============================================

price = stock["Close"].resample("MS").last()

df = pd.DataFrame(price)
df.columns = ["Price"]

df = df.merge(cpi, left_index=True,
              right_index=True,
              how="left")

# Forward fill CPI in case stock data is newer than latest CPI report
df["CPI"] = df["CPI"].ffill()

# Drop rows where CPI is still NaN (before our first CPI data point)
df = df.dropna(subset=["CPI"])

# ============================================
# CALCULATIONS
# ============================================

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

df["Real_Price"] = (
    df["Price"] *
    (base_cpi / df["CPI"])
)

df["Inflation_Dependence"] = (
    df["Inflation_Rate"] /
    df["Nominal_Return"]
)

# ============================================
# CHART 1
# ============================================

fig1 = go.Figure()

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

fig1.update_layout(
    title=f"{ticker} Nominal vs Real Price"
)

st.plotly_chart(fig1, use_container_width=True)

# ============================================
# CHART 2
# ============================================

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

# ============================================
# CHART 3
# ============================================

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

# ============================================
# SUMMARY
# ============================================

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
