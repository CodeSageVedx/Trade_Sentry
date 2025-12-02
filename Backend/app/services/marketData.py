import yfinance as yf
import pandas as pd
import numpy as np
import os

# --- CACHE CLEANUP ---
if os.path.exists('yfinance.cache.sqlite'):
    try:
        os.remove('yfinance.cache.sqlite')
    except Exception:
        pass

def validate_indian_ticker(ticker):
    ticker = ticker.upper().strip().replace(" ", "")
    if not ticker.endswith(".NS") and not ticker.endswith(".BO"):
        ticker = f"{ticker}.NS"
    return ticker

def get_stock_data(ticker, period="2y", interval="1d"):
    ticker = validate_indian_ticker(ticker)
    try:
        # SAFE MODE: Removed 'multi_level_index' argument
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        
        if df.empty: return None

        # Manual MultiIndex Flattening (Works on old & new versions)
        if isinstance(df.columns, pd.MultiIndex):
            try:
                # Try to get level 0 (Price)
                df.columns = df.columns.get_level_values(0)
            except:
                # Fallback: Collapse columns
                df.columns = ['_'.join(col).strip() for col in df.columns.values]

        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        available_cols = [col for col in required_cols if col in df.columns]
        
        if not available_cols: return None
        
        return df[available_cols]

    except Exception as e:
        print(f"Data Fetch Error: {e}")
        return None

def get_full_chart_data(ticker):
    ticker = validate_indian_ticker(ticker)
    datasets = {}
    
    # 1. Intraday (1D)
    df_intra = get_stock_data(ticker, period="5d", interval="1m")
    if df_intra is not None and not df_intra.empty:
        last_active_date = df_intra.index[-1].date()
        daily_mask = df_intra.index.date == last_active_date
        df_1d_clean = df_intra[daily_mask]
        
        datasets['1D'] = df_1d_clean.reset_index().apply(lambda x: {
            "time": x.iloc[0].isoformat(), 
            "open": x['Open'], "high": x['High'], "low": x['Low'], "close": x['Close']
        }, axis=1).tolist()
        
    # 2. Weekly (5D)
    df_5d = get_stock_data(ticker, period="5d", interval="15m")
    if df_5d is not None:
        datasets['5D'] = df_5d.reset_index().apply(lambda x: {
            "time": x.iloc[0].isoformat(), 
            "open": x['Open'], "high": x['High'], "low": x['Low'], "close": x['Close']
        }, axis=1).tolist()

    # 3. Yearly (1Y)
    df_1y = get_stock_data(ticker, period="1y", interval="1d")
    if df_1y is not None:
        datasets['1Y'] = df_1y.reset_index().apply(lambda x: {
            "time": x.iloc[0].isoformat(), 
            "open": x['Open'], "high": x['High'], "low": x['Low'], "close": x['Close']
        }, axis=1).tolist()
        
    return datasets

def get_pivot_points(ticker):
    ticker = validate_indian_ticker(ticker)
    df = get_stock_data(ticker, period="10d", interval="1d")
    
    if df is None or len(df) < 2:
        return None

    try:
        today_candle = df.iloc[-1]
        today_close = float(today_candle['Close'])

        last_candle = df.iloc[-2]
        
        high = float(last_candle['High'])
        low = float(last_candle['Low'])
        close = float(last_candle['Close'])
        
        pivot = (high + low + close) / 3
        r1 = (2 * pivot) - low
        r2 = pivot + (high - low)
        s1 = (2 * pivot) - high
        s2 = pivot - (high - low)
        
        return {
            "symbol": ticker,
            "current_price": round(today_close, 2),
            "pivot_point": round(pivot, 2),
            "resistance": {"target_1": round(r1, 2), "target_2": round(r2, 2)},
            "support": {"stop_1": round(s1, 2), "stop_2": round(s2, 2)}
        }
    except Exception:
        return None
    
if __name__ == "__main__":
    # Test the "Snap-to-Last-Day" logic
    print("Testing Pivot Points for RELIANCE...")
    print(get_pivot_points("RELIANCE"))