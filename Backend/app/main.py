import asyncio
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- APP SETUP ---
app = FastAPI()

origins = [
    "http://localhost:5173",                
    "http://127.0.0.1:5173",                
    "https://trade-sentry-frontend.vercel.app", 
    "*"
]

# --- CORS CONFIGURATION ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATA MODELS ---
class ChatRequest(BaseModel):
    ticker: str
    question: str
    context_data: dict 

# --- ENDPOINTS ---

@app.get("/")
def read_root():
    return {"status": "TradeSentry System Online 🟢"}

@app.get("/api/analyze/{ticker}")
async def analyze_stock(ticker: str):
    """
    Main Dashboard Endpoint.
    Orchestrates fetching data locally and calling AWS for AI analysis.
    """
    print(f"🚀 Analyzing {ticker}...")

    # Lazy imports to keep startup fast
    from app.services.market_data import get_pivot_points, get_stock_data, get_full_chart_data
    from app.services.ai_engine import predict_trend      # Now calls AWS
    from app.services.news_agent import get_news_sentiment # Now calls AWS
    from app.services.llm_engine import get_ai_verdict

    # 1. Math & Chart Data (Local Calculation)
    pivots = get_pivot_points(ticker)
    if not pivots: 
        return {"error": "Invalid Ticker or Data Unavailable"}
   
    chart_data = get_full_chart_data(ticker)

    # 2. Trend Analysis (Calls AWS Lambda)
    # We pass raw price data to the remote AI service
    trend = {"signal": "NEUTRAL", "confidence": 0}
    
    if chart_data and '1Y' in chart_data and len(chart_data['1Y']) > 60:
        closes = [item['close'] for item in chart_data['1Y'][-100:]]
        trend = predict_trend(closes) 

    # 3. Sentiment Analysis (Calls AWS Lambda)
    sentiment = get_news_sentiment(pivots['symbol'])

    # 4. LLM Verdict (Local Logic using Groq API)
    ai_analysis = get_ai_verdict(
        ticker, 
        pivots['current_price'], 
        pivots, 
        trend, 
        sentiment
    )
    
    return {
        "symbol": pivots['symbol'],
        "price": pivots['current_price'],
        "trend_signal": trend,
        "sentiment_signal": sentiment,
        "support_resistance": pivots,
        "ai_analysis": ai_analysis,
        "chart_data": chart_data
    }

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    from app.services.question_agent import get_chat_response
    response = get_chat_response(request.ticker, request.question, request.context_data)
    return {"answer": response}

@app.websocket("/ws/price/{ticker}")
async def websocket_endpoint(websocket: WebSocket, ticker: str):
    await websocket.accept()
    from app.services.market_data import get_pivot_points
    
    try:
        while True:
            data = get_pivot_points(ticker)
            if data:
                await websocket.send_json({
                    "price": data['current_price'],
                    "symbol": data['symbol']
                })
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        print(f"Disconnected client for {ticker}")
    except Exception:
        pass

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)