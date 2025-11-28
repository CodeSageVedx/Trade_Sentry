import yfinance as yf
from transformers import pipeline

# 1. Load FinBERT Sentiment Model (Cached)
try:
    print("Loading FinBERT model...")
    sentiment_pipeline = pipeline("text-classification", model="ProsusAI/finbert")
    print("✅ FinBERT Loaded")
except Exception as e:
    print(f"⚠️ FinBERT Error: {e}")
    sentiment_pipeline = None

def get_news_sentiment(ticker):
    """
    Fetches news headlines and calculates a sentiment score.
    Optimized for Indian Market (NSE) data structure where titles are nested.
    """
    if sentiment_pipeline is None:
        return "Neutral (Model Missing)"

    try:
        # 2. Fetch News
        stock = yf.Ticker(ticker)
        news = stock.news
        
        if not news:
            print(f"ℹ️ No news found for {ticker}")
            return "Neutral (No News)"
            
        # 3. Extract Headlines (Based on your Debug Findings)
        headlines = []
        for item in news[:5]: # Top 5 Articles
            title = None
            
            # CASE 1: Nested 'content' with 'title' (NSE structure)
            if 'content' in item and 'title' in item['content']:
                title = item['content']['title']
            
            # CASE 2: Flat 'title' (Backup for US stocks or Search API results)
            elif 'title' in item:
                title = item['title']
                
            if title:
                headlines.append(title)
        
        if not headlines:
            return "Neutral"

        print(f"📰 Analyzing {len(headlines)} headlines for {ticker}...")

        # 4. Analyze Sentiment
        results = sentiment_pipeline(headlines, truncation=True, max_length=512)
        
        # 5. Calculate Verdict (Weighted Vote)
        score = 0
        for i, res in enumerate(results):
            weight = 2 if i == 0 else 1
            
            if res['label'] == 'positive':
                score += weight
            elif res['label'] == 'negative':
                score -= weight
        
        if score > 0: return "Positive 🟢"
        elif score < 0: return "Negative 🔴"
        else: return "Neutral ⚪"

    except Exception as e:
        print(f"News Error: {e}")
        return "Neutral"

if __name__ == "__main__":
    print(get_news_sentiment("ADANIENT.NS")) 