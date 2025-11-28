import yfinance as yf
import pandas as pd
import numpy as np

def validate_indian_ticker(ticker):
    """Ensures the ticker ends with .NS or .BO"""
    ticker = ticker.upper().strip().replace(" ", "")
    if not ticker.endswith(".NS") and not ticker.endswith(".BO"):
        ticker = f"{ticker}.NS"
    return ticker

def get_stock_data(ticker, period="2y"):
    ticker = validate_indian_ticker(ticker)
    
    try:
        # SIMPLIFIED: Let yfinance handle the session/headers internally
        # usage of custom session is what caused the crash
        df = yf.download(ticker, period=period, progress=False, multi_level_index=False)
        
        if df.empty:
            print(f"No data found for {ticker}")
            return None

        # Ensure we have the right columns
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        
        # Flatten MultiIndex if it exists (common in new yfinance versions)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        # Verify columns exist
        if not all(col in df.columns for col in required_cols):
            return None
            
        return df[required_cols]

    except Exception as e:
        print(f"Data Fetch Error: {e}")
        return None

def get_pivot_points(ticker):
    ticker = validate_indian_ticker(ticker)
    
    # Fetch 10 days to be safe
    df = get_stock_data(ticker, period="10d")
    
    if df is None or len(df) < 2:
        return None

    try:
        # 1. Get Today's Live Price (Last row)
        today_candle = df.iloc[-1]
        today_close = float(today_candle['Close'])

        # 2. Get Yesterday's Completed Candle for Pivot Math (2nd to last row)
        last_candle = df.iloc[-2]
        
        high = float(last_candle['High'])
        low = float(last_candle['Low'])
        close = float(last_candle['Close'])
        
        # 3. Pivot Formulas
        pivot = (high + low + close) / 3
        r1 = (2 * pivot) - low
        r2 = pivot + (high - low)
        s1 = (2 * pivot) - high
        s2 = pivot - (high - low)
        
        return {
            "symbol": ticker,
            "current_price": round(today_close, 2),
            "pivot_point": round(pivot, 2),
            "resistance": {
                "target_1": round(r1, 2),
                "target_2": round(r2, 2)
            },
            "support": {
                "stop_1": round(s1, 2),
                "stop_2": round(s2, 2)
            }
        }
    except Exception as e:
        print(f"Calculation Error: {e}")
        return None

if __name__ == "__main__":
    print(get_pivot_points("RELIANCE"))