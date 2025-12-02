import yfinance as yf
import requests
import os

ML_SERVICE_URL = os.getenv("ML_SERVICE_URL")

def get_news_sentiment(ticker):
    """
    Fetches news locally (lightweight), sends to AWS for FinBERT analysis (heavy).
    """
    try:
        # 1. Fetch News (This is light, Render can handle it)
        stock = yf.Ticker(ticker)
        news = stock.news
        
        headlines = []
        if news:
            for item in news[:5]:
                title = item.get('title') or item.get('content', {}).get('title')
                if title: headlines.append(title)
        
        if not headlines:
            return "Neutral (No News)"

        # 2. If no AWS, stop here
        if not ML_SERVICE_URL:
            return "Neutral (No AI)"

        # 3. Send Headlines to AWS
        payload = {"headlines": headlines}
        response = requests.post(ML_SERVICE_URL, json=payload, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            return result.get('sentiment', "Neutral")
        else:
            return "Neutral"

    except Exception as e:
        print(f"News/AWS Error: {e}")
        return "Neutral"