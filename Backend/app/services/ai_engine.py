import os
import requests
import pandas as pd

# This URL comes from your AWS API Gateway after deployment
ML_SERVICE_URL = os.getenv("ML_SERVICE_URL") 

def predict_trend(historical_prices):
    """
    Sends price history to AWS Lambda for LSTM processing.
    """
    # 1. If no AWS URL is set, return Neutral (Safe Failover)
    if not ML_SERVICE_URL:
        print("⚠️ ML_SERVICE_URL not set. Skipping AI prediction.")
        return {"signal": "NEUTRAL (No AI)", "confidence": 0}

    try:
        # 2. Prepare Payload
        # AWS expects: { "closes": [150.1, 152.3, ...] }
        payload = {"closes": historical_prices}
        
        # 3. Call AWS Lambda
        # 10s timeout prevents Render from hanging if AWS is cold-starting
        response = requests.post(ML_SERVICE_URL, json=payload, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            return result.get('trend', {"signal": "NEUTRAL", "confidence": 0})
        else:
            print(f"AWS Error: {response.status_code} - {response.text}")
            return {"signal": "ERROR", "confidence": 0}
            
    except Exception as e:
        print(f"Connection Error to ML Service: {e}")
        return {"signal": "ERROR", "confidence": 0}