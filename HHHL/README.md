This project fetches ticker symbols showing an uptrend (higher highs), along with their descriptions and stock charts.

🔧 Requirements
1. Install Python
Download from: https://www.python.org/

2. Install dependencies
Run the following command:
pip install pandas yfinance matplotlib requests

3. Get free API keys
Sign up and get your API keys from:

Finnhub
Alpha Vantage
Financial Modeling Prep

4. Configure API keys
Open config.py and replace 'your_api_key' with your actual API keys:

FINNHUB_API_KEY = 'your_api_key'
ALPHA_VANTAGE_API_KEY = 'your_api_key'
FMP_API_KEY = 'your_api_key'

5. Run the project
In your terminal:

python fetchall.py