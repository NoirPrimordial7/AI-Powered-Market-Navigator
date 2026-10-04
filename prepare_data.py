"""Create dated, offline examples from public market data. Run manually, not on page load."""
import json
from pathlib import Path
from datetime import datetime,timezone
import pandas as pd
import requests
import yfinance as yf

ROOT=Path(__file__).resolve().parent
dest=ROOT/'data';dest.mkdir(exist_ok=True)
cache=ROOT/'.cache'/'yfinance';cache.mkdir(parents=True,exist_ok=True)
yf.set_tz_cache_location(str(cache))
manifest_path=dest/'provenance.json'
manifest=json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {}
for ticker in ['AAPL','MSFT','NVDA','SPY','RELIANCE.NS','TCS.NS']:
    try:
        data=yf.Ticker(ticker).history(period='1y',interval='1d',timeout=10,raise_errors=True)
        if len(data)<60:raise ValueError('Insufficient data')
        data.index=data.index.tz_localize(None)
        data=data[['Open','High','Low','Close','Volume']]
        data.index.name='Date';data.to_csv(dest/f'{ticker}.csv')
        manifest[ticker]={'source':'Yahoo Finance via yfinance','first_date':str(data.index[0].date()),'last_date':str(data.index[-1].date()),'fetched_at':datetime.now(timezone.utc).isoformat()}
        print(ticker,len(data),manifest[ticker]['last_date'])
    except Exception as exc:print(ticker,type(exc).__name__)
if 'AAPL' not in manifest or not (dest/'AAPL.csv').exists():
    url='https://raw.githubusercontent.com/plotly/datasets/master/finance-charts-apple.csv'
    response=requests.get(url,timeout=15);response.raise_for_status()
    from io import StringIO
    frame=pd.read_csv(StringIO(response.text))
    data=frame[['Date','AAPL.Open','AAPL.High','AAPL.Low','AAPL.Close','AAPL.Volume']].rename(columns=lambda s:s.replace('AAPL.','')).set_index('Date')
    data.to_csv(dest/'AAPL.csv')
    manifest['AAPL']={'source':'Plotly public example dataset','source_url':url,'first_date':str(data.index[0]),'last_date':str(data.index[-1]),'fetched_at':datetime.now(timezone.utc).isoformat()}
    print('AAPL historical sample saved',len(data))
(dest/'provenance.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
