"""Market data and inference. The original trained model is used unchanged."""
from pathlib import Path
import os
import re
import time
import threading
import sqlite3
from contextlib import closing
from uuid import uuid4
import numpy as np
import pandas as pd
import requests
import streamlit as st
import ta
from sklearn.preprocessing import MinMaxScaler

ROOT=Path(__file__).resolve().parent
FEATURES=['Open','High','Low','Close','Volume','RSI','SMA_20','MACD','MACD_signal','BB_upper','BB_lower']
COMPANIES={'AAPL':'Apple Inc.','MSFT':'Microsoft','NVDA':'NVIDIA','GOOGL':'Alphabet','AMZN':'Amazon','META':'Meta Platforms','TSLA':'Tesla','SPY':'S&P 500 ETF','RELIANCE.NS':'Reliance Industries','TCS.NS':'Tata Consultancy Services','INFY.NS':'Infosys','HDFCBANK.NS':'HDFC Bank'}

def validate_ticker(value):
    value=value.strip().upper()
    if not re.fullmatch(r'[A-Z0-9][A-Z0-9.^-]{0,14}',value):
        raise ValueError('Enter a valid ticker, such as AAPL or RELIANCE.NS.')
    return value

def indicators(data):
    data=data[['Open','High','Low','Close','Volume']].copy()
    if len(data)<60 or data.Close.isna().all():
        raise ValueError('This symbol needs at least 60 daily observations to run the model.')
    data['RSI']=ta.momentum.RSIIndicator(data.Close).rsi()
    data['SMA_20']=ta.trend.SMAIndicator(data.Close,window=20).sma_indicator()
    macd=ta.trend.MACD(data.Close)
    data['MACD']=macd.macd();data['MACD_signal']=macd.macd_signal()
    bands=ta.volatility.BollingerBands(data.Close)
    data['BB_upper']=bands.bollinger_hband();data['BB_lower']=bands.bollinger_lband()
    data['SMA_50']=data.Close.rolling(50).mean()
    data['Drawdown']=(data.Close/data.Close.cummax()-1)*100
    data['Daily_return']=data.Close.pct_change()*100
    return data[FEATURES+['SMA_50','Drawdown','Daily_return']]

def snapshot_symbols():
    return [p.stem for p in sorted((ROOT/'data').glob('*.csv'))]

@st.cache_data(ttl=900,max_entries=50,show_spinner=False)
def get_data(ticker, source='Historical example'):
    ticker=validate_ticker(ticker)
    if source=='Historical example':
        path=ROOT/'data'/f'{ticker}.csv'
        if not path.exists():
            raise ValueError('There is no saved example for this symbol. Switch to live data to analyze it.')
        frame=pd.read_csv(path,index_col=0,parse_dates=True)
        frame.attrs['currency']='INR' if ticker.endswith(('.NS','.BO')) else 'USD'
    else:
        import yfinance as yf
        cache=ROOT/'.cache'/'yfinance';cache.mkdir(parents=True,exist_ok=True)
        yf.set_tz_cache_location(str(cache))
        instrument=yf.Ticker(ticker)
        frame=instrument.history(period='1y',interval='1d',timeout=12,raise_errors=True)
        if frame.empty:
            raise ValueError('No price history was returned. Check the symbol or try the historical example.')
        frame.index=frame.index.tz_localize(None)
        frame.attrs['currency']=(instrument.history_metadata or {}).get('currency','Quote units')
    return indicators(frame)

@st.cache_resource(show_spinner=False)
def model_resource():
    os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL','2')
    os.environ.setdefault('TF_NUM_INTRAOP_THREADS','2')
    os.environ.setdefault('TF_NUM_INTEROP_THREADS','1')
    from keras.models import load_model
    model=load_model(str(ROOT/'model3.h5'),compile=False)
    return model,threading.Lock()

def predict(data):
    model,lock=model_resource()
    rows,features=model.input_shape[1:]
    if features!=len(FEATURES):
        raise ValueError('The model input does not match the available feature set.')
    clean=data[FEATURES].copy().ffill().fillna(0)
    if not np.isfinite(clean.to_numpy()).all():
        raise ValueError('Price history contains invalid observations.')
    if len(clean)<rows:
        raise ValueError(f'The model needs {rows} trading sessions.')
    # Retains the original app's per-history scaling. Training scaler is absent.
    scaler=MinMaxScaler()
    scaled=scaler.fit_transform(clean)
    tensor=scaled[-rows:].astype('float32').reshape(1,rows,features)
    with lock:
        prediction=float(np.asarray(model(tensor,training=False))[0,0])
    last=scaled[-1].copy();last[FEATURES.index('Close')]=prediction
    price=float(scaler.inverse_transform(last.reshape(1,-1))[0,FEATURES.index('Close')])
    if not np.isfinite(price) or price<=0:
        raise ValueError('The model returned an unusable estimate for this symbol.')
    return price

@st.cache_data(ttl=900,max_entries=50,show_spinner=False)
def analyze(ticker,source):
    data=get_data(ticker,source)
    return data,predict(data)

def claim_request():
    """Bound total costly work across all visitors on this single-instance demo."""
    identity=st.session_state.setdefault('visitor_id',str(uuid4()))
    cache=ROOT/'.cache';cache.mkdir(exist_ok=True)
    now=time.time()
    with closing(sqlite3.connect(cache/'limits.sqlite',timeout=5)) as conn, conn:
        conn.execute('CREATE TABLE IF NOT EXISTS requests (visitor TEXT, ts REAL)')
        conn.execute('BEGIN IMMEDIATE')
        conn.execute('DELETE FROM requests WHERE ts < ?',(now-86400,))
        visitor_count=conn.execute('SELECT COUNT(*) FROM requests WHERE visitor=? AND ts>?',(identity,now-60)).fetchone()[0]
        global_count=conn.execute('SELECT COUNT(*) FROM requests WHERE ts>?',(now-3600,)).fetchone()[0]
        if visitor_count>=5:
            raise ValueError('You have reached 5 analyses this minute. Please wait a moment.')
        if global_count>=120:
            raise ValueError('The demo has reached its hourly analysis limit. The historical overview is still available.')
        conn.execute('INSERT INTO requests VALUES (?,?)',(identity,now))

def describe(data,prediction):
    last=data.iloc[-1];change=(prediction/float(last.Close)-1)*100
    rsi=float(last.RSI)
    momentum='elevated' if rsi>70 else 'subdued' if rsi<30 else 'in the middle of its usual range'
    macd='above' if last.MACD>last.MACD_signal else 'below'
    trend='above' if last.Close>last.SMA_20 else 'below'
    return [f'The model estimates a {abs(change):.2f}% {"increase" if change>=0 else "decrease"} from the last closing price. This is a model output, not a measured probability.',f'RSI is {rsi:.1f}, placing recent momentum {momentum}. MACD is {macd} its signal line.',f'The closing price is {trend} its 20-day moving average. Compare this trend with the forecast rather than relying on either alone.']

def secret(name):
    value=os.getenv(name)
    if value:return value
    try:return st.secrets.get(name,'')
    except (FileNotFoundError,st.errors.StreamlitSecretNotFoundError):return ''

@st.cache_data(ttl=1800,max_entries=30,show_spinner=False)
def sentiments(ticker):
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    vader=SentimentIntensityAnalyzer(); results={}
    news_key=secret('NEWS_API_KEY')
    if news_key:
        try:
            r=requests.get('https://newsapi.org/v2/everything',headers={'X-Api-Key':news_key},params={'q':f'{ticker} stock','language':'en','pageSize':12},timeout=10)
            r.raise_for_status();articles=r.json().get('articles',[])
            if articles:results['News']={'score':float(np.mean([vader.polarity_scores(f"{a.get('title') or ''} {a.get('description') or ''}")['compound'] for a in articles])),'count':len(articles)}
        except requests.RequestException:results['News']={'error':'News data is temporarily unavailable.'}
    client=secret('REDDIT_CLIENT_ID');key=secret('REDDIT_CLIENT_SECRET')
    if client and key:
        try:
            headers={'User-Agent':'market-navigator/1.0 by NoirPrimordial7'}
            r=requests.post('https://www.reddit.com/api/v1/access_token',auth=(client,key),data={'grant_type':'client_credentials'},headers=headers,timeout=10)
            r.raise_for_status();headers['Authorization']='Bearer '+r.json()['access_token']
            r=requests.get('https://oauth.reddit.com/r/stocks/search',headers=headers,params={'q':ticker,'restrict_sr':'on','limit':20,'sort':'new'},timeout=10)
            r.raise_for_status();posts=r.json()['data']['children']
            if posts:results['Reddit']={'score':float(np.mean([vader.polarity_scores(p['data']['title'])['compound'] for p in posts])),'count':len(posts)}
        except (requests.RequestException,KeyError):results['Reddit']={'error':'Reddit data is temporarily unavailable.'}
    return results
