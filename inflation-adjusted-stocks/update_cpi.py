import pandas as pd
import os
import requests
from io import StringIO
import time

def update_cpi():
    print("Updating CPI data from FRED...")

    # FRED URL for CPIAUCSNS (Consumer Price Index for All Urban Consumers: All Items in U.S. City Average, Not Seasonally Adjusted)
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSNS"

    # Using a common browser User-Agent to avoid simple bot detection
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/csv,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    try:
        # FRED sometimes has issues with automated tools; we try to be polite
        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code != 200:
            print(f"Failed to fetch data from FRED. Status code: {response.status_code}")
            if response.status_code == 403:
                print("Access denied. FRED might be blocking this request.")
            return

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

        # Filter for quarterly data (Jan 1, Apr 1, Jul 1, Oct 1)
        # FRED data points are usually on the 1st of the month
        filtered_new = new_data[new_data['Date'].dt.month.isin([1, 4, 7, 10])].copy()

        # Always include the absolute latest available data point too
        latest_datapoint = new_data.iloc[[-1]].copy()
        combined_new = pd.concat([filtered_new, latest_datapoint]).drop_duplicates(subset=['Date'])

        # Merge with existing
        final_df = pd.concat([existing_df, combined_new]).drop_duplicates(subset=['Date'], keep='last')
        final_df = final_df.sort_values('Date')

        # Formatting for CSV
        final_df['Date'] = final_df['Date'].dt.strftime('%Y-%m-%d')
        final_df['CPI'] = final_df['CPI'].apply(lambda x: f"{x:.3f}" if isinstance(x, (int, float)) else x)

        # Save back to CSV
        final_df.to_csv(csv_path, index=False)
        print(f"Successfully updated {csv_path}. Latest date: {final_df['Date'].iloc[-1]}")

    except Exception as e:
        print(f"An error occurred while updating CPI: {e}")

if __name__ == "__main__":
    update_cpi()
