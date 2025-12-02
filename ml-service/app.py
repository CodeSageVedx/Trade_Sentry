import json
import numpy as np
import pandas as pd
import tensorflow as tf
import joblib
from transformers import pipeline
from sklearn.preprocessing import MinMaxScaler
import os

# --- 1. GLOBAL LOADING (Warm Start) ---
print("⏳ Loading Models...")

try:
    lstm_model = tf.keras.models.load_model("lstm_model.h5")
    print("✅ LSTM Model Loaded")
except:
    lstm_model = None

try:
    scaler = joblib.load("scaler.gz")
    print("✅ Scaler Loaded")
except:
    scaler = None

try:
    sentiment_pipe = pipeline("text-classification", model="ProsusAI/finbert")
    print("✅ FinBERT Loaded")
except:
    sentiment_pipe = None

# --- 2. LOGIC ---
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def predict_trend(historical_prices):
    if lstm_model is None or scaler is None:
        return {"signal": "ERROR (Model Missing)", "confidence": 0}

    try:
        df = pd.DataFrame(historical_prices, columns=['Close'])
        df['Return'] = df['Close'].pct_change()
        df['RSI'] = calculate_rsi(df['Close'])
        df.dropna(inplace=True)
        
        if len(df) < 60:
            return {"signal": "INSUFFICIENT_DATA", "confidence": 0}
            
        data = df[['Return', 'RSI']].tail(60).values
        
        local_scaler = MinMaxScaler(feature_range=(-1, 1))
        scaled_data = local_scaler.fit_transform(data)
        X_input = np.array([scaled_data])
        
        prediction = lstm_model.predict(X_input, verbose=0)
        prob = float(prediction[0][0])
        
        if prob > 0.5:
            return {"signal": "BULLISH", "confidence": round(prob * 100, 2)}
        else:
            return {"signal": "BEARISH", "confidence": round((1 - prob) * 100, 2)}
    except:
        return {"signal": "ERROR", "confidence": 0}

def analyze_news(headlines):
    if sentiment_pipe is None or not headlines:
        return "Neutral"
    try:
        results = sentiment_pipe(headlines, truncation=True, max_length=512)
        score = 0
        for i, res in enumerate(results):
            weight = 2 if i == 0 else 1
            if res['label'] == 'positive': score += weight
            elif res['label'] == 'negative': score -= weight
        if score > 0: return "Positive 🟢"
        elif score < 0: return "Negative 🔴"
        else: return "Neutral ⚪"
    except:
        return "Neutral"

def lambda_handler(event, context):
    try:
        body = json.loads(event['body']) if 'body' in event else event
        response_data = {}
        
        if 'closes' in body:
            prices = [float(x) for x in body['closes']]
            response_data['trend'] = predict_trend(prices)
            
        if 'headlines' in body:
            response_data['sentiment'] = analyze_news(body['headlines'])
            
        return {
            'statusCode': 200,
            'body': json.dumps(response_data),
            'headers': {'Content-Type': 'application/json'}
        }
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({"error": str(e)})}