import os
import requests
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import datetime
from io import BytesIO
import base64
import webbrowser

# Import the user's API keys from config.py
try:
    from config import FINNHUB_API_KEY, FMP_API_KEY
except ImportError:
    FINNHUB_API_KEY = None
    FMP_API_KEY = None

# Ensure the API keys are provided
if not FINNHUB_API_KEY:
    raise ValueError("Please provide your Finnhub API key in config.py")
if not FMP_API_KEY:
    raise ValueError("Please provide your Financial Modeling Prep API key in config.py")

# Define the limit for the number of symbols to process
SYMBOLS_LIMIT = 50

# Define criteria
sectors = []
max_price = 100
min_listing_date = datetime.datetime.now() - datetime.timedelta(days=365*30)

# Define the path for the result folder
result_folder = os.path.join(os.path.dirname(__file__), "result")
os.makedirs(result_folder, exist_ok=True)

# Initialize list to store data for HTML report
html_data = []

# Function to fetch stock data
def fetch_stock_data(ticker):
    stock = yf.Ticker(ticker)
    return stock.history(period="max")

# Function to identify uptrend over the last month
def is_uptrend(df):
    if df.empty or len(df) < 30:
        print("Insufficient data for uptrend analysis")
        return False

    df['High_diff'] = df['High'].diff()
    df['Low_diff'] = df['Low'].diff()
    print(f"High differences:", df['High_diff'].tail(30))
    print(f"Low differences:", df['Low_diff'].tail(30))

    higher_highs = df['High_diff'] > 0
    higher_lows = df['Low_diff'] > 0
    print(f"Higher highs:", higher_highs.tail(30))
    print(f"Higher lows:", higher_lows.tail(30))

    return higher_highs.tail(30).sum() >= 2 and higher_lows.tail(30).sum() >= 2

# Function to generate base64 encoded image from matplotlib figure
def generate_base64_image(fig):
    buf = BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    base64_image = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    return base64_image

# Function to create and encode stock data graph
def create_encoded_stock_graph(df, ticker, exchange):
    plt.figure(figsize=(10, 5))
    plt.plot(df['Close'], label='Close Price')
    plt.title(f'{exchange}_{ticker} Stock Price')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()

    base64_image = generate_base64_image(plt.gcf())
    plt.close()

    return base64_image

# Function to fetch additional company details from FMP
def fetch_company_details(ticker):
    url = f'https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={FMP_API_KEY}'
    response = requests.get(url)
    if response.status_code == 200:
        company_details = response.json()
        if company_details:
            return company_details[0]
    print(f"Error fetching company details for {ticker}: {response.status_code}")
    return {}

# Function to filter stocks based on criteria
def filter_stocks(limit=SYMBOLS_LIMIT):
    filtered_stocks = []

    url = f'https://finnhub.io/api/v1/stock/symbol?exchange=US&token={FINNHUB_API_KEY}'
    response = requests.get(url)
    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.content.decode('utf-8')}")

    if response.status_code != 200:
        print("Error fetching stock symbols")
        return []

    try:
        stocks = response.json()
        print(f"Parsed JSON type: {type(stocks)}")
        print(f"Parsed JSON: {stocks[:5]}")  # Print only the first 5 items for brevity
    except ValueError as e:
        print(f"Error parsing JSON: {e}")
        return []

    if not isinstance(stocks, list):
        print("Error: Expected a list of stocks")
        return []

    for i, stock in enumerate(stocks):
        if i >= limit:
            break

        symbol = stock.get('symbol')
        description = stock.get('description')

        # Get company profile to check sector and IPO date
        profile_url = f'https://finnhub.io/api/v1/stock/profile2?symbol={symbol}&token={FINNHUB_API_KEY}'
        profile_response = requests.get(profile_url)
        profile = profile_response.json()
        print(f"Profile for {symbol}: {profile}")

        if not profile:
            continue

        ipo_date_str = profile.get('ipo', None)
        sector = profile.get('finnhubIndustry', None)
        exchange = profile.get('exchange', 'UNKNOWN')
        current_price_url = f'https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}'
        current_price_response = requests.get(current_price_url)
        current_price = current_price_response.json().get('c', 0)

        print(f"Symbol: {symbol}, Sector: {sector}, Exchange: {exchange}, IPO Date: {ipo_date_str}, Current Price: {current_price}")

        if ipo_date_str is None:
            print(f"Excluded {symbol} because IPO date is missing.")
            continue

        if current_price == 0:
            print(f"Excluded {symbol} because current price is 0.")
            continue

        if current_price > max_price:
            print(f"Excluded {symbol} because current price {current_price} exceeds max price {max_price}.")
            continue

        try:
            ipo_date = datetime.datetime.strptime(ipo_date_str, '%Y-%m-%d')
        except ValueError:
            print(f"Invalid IPO date format for {symbol}: {ipo_date_str}")
            continue

        if ipo_date <= min_listing_date:
            print(f"Excluded {symbol} because IPO date {ipo_date} is before minimum listing date {min_listing_date}.")
            continue

        # Fetch additional company details from FMP
        company_details = fetch_company_details(symbol)
        profile.update(company_details)

        filtered_stocks.append((symbol, exchange, profile, current_price))
        print(f"Included {symbol}")

    return filtered_stocks

# Get the filtered list of stocks
filtered_stock_tickers = filter_stocks()
print(f"Filtered stock tickers: {filtered_stock_tickers}")

# Check each stock and save the graph if it's in uptrend
for ticker, exchange, profile, current_price in filtered_stock_tickers:
    data = fetch_stock_data(ticker)
    if not data.empty:
        if is_uptrend(data):
            base64_image = create_encoded_stock_graph(data, ticker, exchange)
            html_data.append({
                'ticker': ticker,
                'exchange': exchange,
                'profile': profile,
                'base64_image': base64_image,
                'current_price': current_price
            })
        else:
            print(f"{ticker} is not in an uptrend")
    else:
        print(f"No data found for {ticker}")

# Generate a unique filename for the HTML report
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
html_filename = os.path.join(result_folder, f"stock_report_{timestamp}.html")

# Generate HTML report
html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stock Report</title>
    <style>
        body { font-family: Arial, sans-serif; }
        .stock-item { margin-bottom: 20px; }
        .stock-item img { max-width: 300px; height: auto; cursor: pointer; }
        .stock-item img:hover { opacity: 0.8; }
    </style>
    <script>
        function openGraph(dataUrl) {
            var win = window.open();
            win.document.write('<iframe src="' + dataUrl + '" frameborder="0" style="border:0; width:100%; height:100%;" allowfullscreen></iframe>');
        }
    </script>
</head>
<body>
    <h1>Stock Report</h1>
    <div class="stock-list">
"""

for item in html_data:
    profile = item['profile']
    data_url = f"data:image/png;base64,{item['base64_image']}"
    html_content += f"""
    <div class="stock-item">
        <h2>{profile.get('companyName', 'N/A')} ({item['ticker']}) - {item['exchange']}</h2>
        <p><strong>Company:</strong> {profile.get('companyName', 'N/A')}</p>
        <p><strong>Sector:</strong> {profile.get('sector', 'N/A')}</p>
        <p><strong>Current Price:</strong> ${item['current_price']}</p>
        <p><strong>IPO Date:</strong> {profile.get('ipoDate', 'N/A')}</p>
        <p><strong>Website:</strong> <a href="{profile.get('website', '#')}" target="_blank">{profile.get('website', 'N/A')}</a></p>
        <p><strong>Description:</strong> {profile.get('description', 'N/A')}</p>
        <img src="{data_url}" alt="{item['ticker']} Stock Price" onclick="openGraph('{data_url}')">
    </div>
    """

html_content += """
    </div>
</body>
</html>
"""

# Save the HTML report
with open(html_filename, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"HTML report saved at {html_filename}")

webbrowser.open(f"file://{html_filename}")
