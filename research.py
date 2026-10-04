"""Research calculations adapted from the Northstar workspace."""
from io import BytesIO
import numpy as np
import pandas as pd
from market import indicators,validate_ticker

PERIODS={'1 month':22,'3 months':63,'6 months':126,'1 year':252}

def read_prices(content):
    if len(content)>5_000_000:raise ValueError('Use a CSV smaller than 5 MB.')
    try:frame=pd.read_csv(BytesIO(content))
    except (ValueError,UnicodeDecodeError,pd.errors.ParserError):raise ValueError('This file could not be read as a price CSV.') from None
    if 'Date' not in frame:raise ValueError('Include a Date column and Open, High, Low, Close, Volume.')
    required=['Open','High','Low','Close','Volume']
    if not set(required).issubset(frame):raise ValueError('Include Open, High, Low, Close, and Volume columns.')
    dates=pd.to_datetime(frame.pop('Date'),errors='coerce',utc=True)
    if dates.isna().any() or dates.duplicated().any():raise ValueError('Every date must be valid and unique.')
    frame=frame[required].apply(pd.to_numeric,errors='coerce')
    if not np.isfinite(frame.to_numpy()).all():raise ValueError('Prices and volume must be finite numbers without blank cells.')
    if (frame[required[:4]]<=0).any().any() or (frame.Volume<0).any():raise ValueError('Prices must be positive; volume cannot be negative.')
    if ((frame.High<frame[['Open','Low','Close']].max(axis=1))|(frame.Low>frame[['Open','High','Close']].min(axis=1))).any():
        raise ValueError('High must cover Open and Close; Low must be below them.')
    frame.index=pd.DatetimeIndex(dates).tz_convert(None);frame.index.name='Date'
    return indicators(frame.sort_index())

def summary(data):
    returns=data.Close.pct_change().dropna()
    return {'return':float((data.Close.iloc[-1]/data.Close.iloc[0]-1)*100),
            'volatility':float(returns.std()*np.sqrt(252)*100),
            'drawdown':float((data.Close/data.Close.cummax()-1).min()*100),
            'volume':float(data.Volume.iloc[-1]),'high':float(data.High.max()),'low':float(data.Low.min())}

def scenario_paths(data,days=20,simulations=400):
    if not isinstance(days,int) or not 5<=days<=60:raise ValueError('Choose 5–60 trading sessions.')
    if not 100<=simulations<=1000:raise ValueError('Choose 100–1,000 simulation paths.')
    returns=np.log(data.Close).diff().dropna().tail(252)
    if len(returns)<30 or not np.isfinite(returns).all():raise ValueError('At least 30 valid daily returns are needed.')
    rng=np.random.default_rng(42)
    paths=float(data.Close.iloc[-1])*np.exp(np.cumsum(rng.normal(returns.mean(),returns.std(),(days,simulations)),axis=0))
    return pd.DataFrame(np.quantile(paths,[.1,.5,.9],axis=1).T,
                        columns=['Lower 10%','Median','Upper 90%'],
                        index=pd.bdate_range(data.index[-1]+pd.offsets.BDay(1),periods=days))

def aligned_prices(frames,days=126):
    if len(frames)<2:raise ValueError('Choose at least two stocks for comparison.')
    prices=pd.concat({symbol:frame.Close for symbol,frame in frames.items()},axis=1,join='inner').dropna().tail(days)
    if len(prices)<2:raise ValueError('These stocks need at least two shared trading dates.')
    return prices,prices.div(prices.iloc[0]).mul(100)

def shortlist():
    import streamlit as st
    from market import snapshot_symbols
    saved=st.query_params.get('watch')
    if saved is not None and saved!=st.session_state.get('watch_query_seen'):
        try:
            items=list(dict.fromkeys(validate_ticker(x) for x in saved.split(',') if x.strip()))
            if len(items)<=8:st.session_state['shortlist']=items
        except ValueError:pass
        st.session_state['watch_query_seen']=saved
    return st.session_state.setdefault('shortlist',snapshot_symbols()[:6])

def save_shortlist(items):
    import streamlit as st
    value=','.join(items)
    st.session_state['shortlist']=items
    st.session_state['watch_query_seen']=value
    st.query_params['watch']=value

def add_symbol(value):
    symbol=validate_ticker(value);items=shortlist()
    if symbol in items:raise ValueError('That symbol is already in your watchlist.')
    if len(items)>=8:raise ValueError('This demo supports up to eight watchlist symbols. Remove one to make room.')
    save_shortlist(items+[symbol])
    return symbol
