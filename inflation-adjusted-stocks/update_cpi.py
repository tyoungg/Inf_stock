import pandas as pd
import os
import requests
from io import StringIO
import time

def update_cpi():
    """
    Fetches the latest CPI data from FRED and updates the local cpi.csv file.
    Returns:
        tuple: (success (bool), message (str))
    """
    # FRED URL for CPIAUCSNS (Consumer Price Index for All Urban Consumers: All Items in U.S. City Average, Not Seasonally Adjusted)
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSNS"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/csv,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    }

    try:
        # Use a short timeout for automated checks
        response = requests.get(url, headers=headers, timeout=5)

        if response.status_code != 200:
            return False, f"FRED returned status {response.status_code}"

        # Load the data into a DataFrame
        new_data = pd.read_csv(StringIO(response.text))
        new_data.columns = ['Date', 'CPI']
        new_data['Date'] = pd.to_datetime(new_data['Date'])

        # Path to the local CSV file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(current_dir, "inflation_data/cpi.csv")

        # Load existing data
        if os.path.exists(csv_path):
            existing_df = pd.read_csv(csv_path)
            existing_df['Date'] = pd.to_datetime(existing_df['Date'])
        else:
            existing_df = pd.DataFrame(columns=['Date', 'CPI'])

        # Merge with existing
        final_df = pd.concat([existing_df, new_data]).drop_duplicates(subset=['Date'], keep='last')
        final_df = final_df.sort_values('Date')

        # Formatting for CSV
        final_df['Date'] = final_df['Date'].dt.strftime('%Y-%m-%d')
        final_df['CPI'] = final_df['CPI'].apply(lambda x: f"{x:.3f}")

        # Save back to CSV
        final_df.to_csv(csv_path, index=False)
        return True, f"Updated. Latest: {final_df['Date'].iloc[-1]}"

    except requests.exceptions.Timeout:
        return False, "Connection timeout (FRED is slow)"
    except Exception as e:
        return False, str(e)

if __name__ == "__main__":
    success, msg = update_cpi()
    print(msg)
