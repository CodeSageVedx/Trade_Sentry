import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yfinance as yf

# 1. Data Engine (Math & Prices)
from app.services.marketData import get_pivot_points, get_stock_data
# 2. AI Models (LSTM Trend)
from app.services.ai_engine import predict_trend
# 3. News Agent (FinBERT Sentiment)
from app.services.news_agent import get_news_sentiment
# 4. LLM Analysis (The Verdict)
from app.services.llm_engine import get_ai_verdict
# 5. Chatbot (Q&A)
from app.services.question_agent import get_chat_response

app = FastAPI()
# --- MIDDLEWARE ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
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
    Main Dashboard Endpoint:
    Fetches Price + Math + Trend + News + AI Verdict in one go.
    """
    print(f"🚀 Analyzing {ticker}...")

    pivots = get_pivot_points(ticker)
    if not pivots: 
        return {"error": "Invalid Ticker or Data Unavailable"}
    # 2. Trend Analysis (AI Engine)
    hist = get_stock_data(ticker, period="1y")
    
    if hist is not None and len(hist) > 60:
        closes = hist['Close'].tail(100).values.tolist()
        trend = predict_trend(closes)
    else:
        trend = {"signal": "NEUTRAL", "confidence": 0}
        
    # 3. Sentiment (News Agent)
    sentiment = get_news_sentiment(pivots['symbol'])

    # 4. LLM Verdict (The Boss)
    ai_analysis = get_ai_verdict(
        ticker, 
        pivots['current_price'], 
        pivots, 
        trend, 
        sentiment
    )
    
    # Final JSON Response
    return {
        "symbol": pivots['symbol'],
        "price": pivots['current_price'],
        "trend_signal": trend,
        "sentiment_signal": sentiment,
        "support_resistance": pivots,
        "ai_analysis": ai_analysis
    }

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Chatbot Endpoint:
    Answers user questions using the context from the analysis.
    """
    response = get_chat_response(request.ticker, request.question, request.context_data)
    return {"answer": response}

@app.websocket("/ws/price/{ticker}")
async def websocket_endpoint(websocket: WebSocket, ticker: str):
    """
    Live Price Stream:
    Simulates a real-time feed by polling Yahoo every 2 seconds.
    """
    await websocket.accept()
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
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass