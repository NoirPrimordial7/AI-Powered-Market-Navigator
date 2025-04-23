import os
import yfinance as yf
import ta
import praw
from newsapi import NewsApiClient
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd
import numpy as np
from tensorflow.keras.models import load_model
from sklearn.preprocessing import MinMaxScaler
import requests
from dotenv import load_dotenv

# Load API keys from .env
load_dotenv()
DEEPSEEK_API_KEY = "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"

analyzer = SentimentIntensityAnalyzer()

def authenticate_reddit():
    return praw.Reddit(
        client_id="zfrvUgWcEwdiDgIQbxBhsA",
        client_secret="4w1eBPimyNn7cP7kGFkdtutfEg27Tg",
        user_agent="ai_market_trend_analyzer"
    )

class RealTimeData:
    def __init__(self):
        self.news_api = NewsApiClient(api_key='2b3fa29c202447c28ff4a738dae7bf39')

    def get_reddit_sentiment(self, ticker, max_posts=199):
        reddit = authenticate_reddit()
        subreddits = ["stocks", "investing", "wallstreetbets", "StockMarket"]
        sentiments = []

        for sub in subreddits:
            subreddit = reddit.subreddit(sub)
            for post in subreddit.search(ticker, limit=max_posts // len(subreddits)):
                sentiments.append(analyzer.polarity_scores(post.title)["compound"])

        return np.mean(sentiments) if sentiments else 0.0

    def get_news_sentiment(self, ticker, max_articles=100):
        try:
            news = self.news_api.get_everything(q=f"{ticker} stock", language='en', page_size=max_articles)
            sentiments = []
            for article in news['articles']:
                title = article.get("title") or ""
                desc = article.get("description") or ""
                sentiments.append(analyzer.polarity_scores(f"{title} {desc}")["compound"])
            return np.mean(sentiments) if sentiments else 0.0
        except Exception as e:
            print(f"News sentiment error: {e}")
            return 0.0

def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    data = stock.history(period="1y", interval="1d")
    data['RSI'] = ta.momentum.RSIIndicator(data['Close']).rsi()
    data['SMA_20'] = ta.trend.SMAIndicator(data['Close'], window=20).sma_indicator()
    macd = ta.trend.MACD(data['Close'])
    data['MACD'] = macd.macd()
    data['MACD_signal'] = macd.macd_signal()
    bb = ta.volatility.BollingerBands(data['Close'])
    data['BB_upper'] = bb.bollinger_hband()
    data['BB_lower'] = bb.bollinger_lband()
    data['Price_Movement'] = data['Close'].diff().fillna(0)
    return data[['Open', 'High', 'Low', 'Close', 'Volume',
                 'RSI', 'SMA_20', 'MACD', 'MACD_signal',
                 'BB_upper', 'BB_lower']]

def preprocess_data(data):
    data = data.copy().ffill().fillna(0)
    numeric_data = data.select_dtypes(include=[np.number])
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(numeric_data)
    X = np.reshape(scaled_data, (1, scaled_data.shape[0], scaled_data.shape[1]))
    return X, scaler, numeric_data.columns

def generate_intelligent_reasoning(data, prediction_price, sentiment_data):
    rsi_value = data['RSI'].iloc[-1]
    macd_value = data['MACD'].iloc[-1]
    macd_signal = data['MACD_signal'].iloc[-1]
    bb_upper = data['BB_upper'].iloc[-1]
    bb_lower = data['BB_lower'].iloc[-1]

    news_sentiment = sentiment_data['news_sentiment']
    reddit_sentiment = sentiment_data['reddit_sentiment']

    prompt = f"""
    I am predicting the next closing price of a stock. Below are the inputs:
    - RSI: {rsi_value}, MACD: {macd_value}, MACD Signal: {macd_signal}, BB Upper: {bb_upper}, BB Lower: {bb_lower}
    - News Sentiment: {news_sentiment}, Reddit Sentiment: {reddit_sentiment}
    - The predicted next closing price is: ${prediction_price:.2f}

    Please provide a natural language explanation for this prediction. Include the following:
    1. Intelligent reasoning based on technical indicators (e.g., RSI, MACD).
    2. Sentiment analysis reasoning (e.g., negative sentiment from news and Reddit).
    3. A confidence score.
    4. A suggestion on whether to buy, hold, or sell based on this information.

    Response in the following format:
    - Explanation: [Your reasoning here]
    - Confidence Score: [Confidence here]
    - Recommendation: [Buy/Hold/Sell]
    """

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {'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'}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai/gpt-4o",
        "messages": [
            {"role": "system", "content": "You are a financial assistant specialized in stock market analysis."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 300
    }

    print("Sending request to OpenRouter API with payload:", payload)  # Debugging line
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}, {response.text}")  # Debugging line to see the full error message

    try:
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        print("AI reasoning generation failed:", e)
        return "Unable to generate explanation at this time. Please try again later."



def predict_stock_movement_with_reasoning(ticker):
    historical_data = get_stock_data(ticker)
    rt_data = RealTimeData()
    news_sentiment = rt_data.get_news_sentiment(ticker)
    reddit_sentiment = rt_data.get_reddit_sentiment(ticker)
    sentiment_data = {
        "news_sentiment": news_sentiment,
        "reddit_sentiment": reddit_sentiment
    }

    X, scaler, feature_columns = preprocess_data(historical_data)
    model = load_model("model3.h5")
    prediction = model.predict(X)
    close_idx = list(feature_columns).index('Close')
    last_row = X[0, -1, :].copy()
    last_row[close_idx] = prediction[0, 0]
    prediction_price = scaler.inverse_transform([last_row])[0, close_idx]
    reasoning_output = generate_intelligent_reasoning(historical_data, prediction_price, sentiment_data)

    return {
        "prediction_price": prediction_price,
        "reasoning": reasoning_output,
        "sentiment": {
            "news": news_sentiment,
            "reddit": reddit_sentiment
        }
    }
print("Prediction and reasoning generated successfully.")

if __name__ == "__main__":
    ticker = input("Enter Stock Ticker (e.g., AAPL): ").strip().upper()
    predict_stock_movement_with_reasoning(ticker)
    response = requests.post(url, json=payload)
    print(response.json())  # Log the entire response to see the structure and error messages
    
