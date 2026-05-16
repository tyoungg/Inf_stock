# Inflation Adjusted Stock Analysis

This application allows you to analyze stock prices adjusted for inflation using US CPI data.

## Features
- Compare nominal vs real (inflation-adjusted) stock prices.
- Compare nominal vs real returns.
- Analyze the inflation dependence ratio of a stock.

## Installation

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the Streamlit application:
   ```bash
   streamlit run app.py
   ```

## Updating CPI Data
To update the inflation data with the latest values from FRED (Federal Reserve Economic Data), run:
```bash
python update_cpi.py
```
This script will fetch the latest Consumer Price Index (CPI) and update `inflation_data/cpi.csv`.

## Project Structure
- `app.py`: Main application script.
- `update_cpi.py`: Utility script to update CPI data from FRED.
- `inflation_data/cpi.csv`: Historical US CPI data.
- `requirements.txt`: List of dependencies.
- `README.md`: Project documentation.
