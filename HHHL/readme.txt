1. install python

2. install other stuff using command below.
pip install pandas yfinance matplotlib requests

3. get free API key from https://finnhub.io/
and 
https://www.alphavantage.co/
and
https://site.financialmodelingprep.com/

4. edit config.py. replace your_api_key with your api key.
FINNHUB_API_KEY = 'your_api_key'
ALPHA_VANTAGE_API_KEY ='your_api_key'
FMP_API_KEY = 'your_api_key'


5. run the command below.
python fetchall.py