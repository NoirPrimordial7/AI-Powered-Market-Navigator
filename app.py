"""Overview: an editorial introduction with a real, dated market study."""
from html import escape
import streamlit as st
from ui import shell,html,footer,section,plot,chart,panel_header,money,sparkline,metric_cards,compact
from market import get_data,analyze,snapshot_symbols,COMPANIES
from news import get_brief,render_brief
from research import summary

shell('Overview')
html('''<section class="hero"><div><div class="eyebrow"><span class="status-dot"></span>Your independent research desk</div><h1>Less noise.<br><em>More perspective.</em></h1></div><div class="hero-aside"><div class="hero-index">01 — FIND YOUR BEARINGS</div><p>Follow the price. Understand the risk. Read the stories behind the movement. A considered space for your next market question.</p><a class="text-link" href="/Analyzer" target="_self">Enter the research studio <span>↗</span></a></div></section><div class="hero-bottom"><div class="capabilities"><span>PRICE & MOMENTUM</span><span>RISK & SCENARIOS</span><span>NEWS & CATALYSTS</span></div><span class="folio">NORTHSTAR / A PROJECT BY ADITYA</span></div>''')

symbols=snapshot_symbols()
if symbols:
    featured='AAPL' if 'AAPL' in symbols else symbols[0]
    data=get_data(featured)
    try:_,prediction=analyze(featured,'Historical example')
    except Exception:prediction=None
    stats=summary(data.tail(126))
    html(f'<div class="desk-label"><span>ON THE DESK / {escape(featured)}</span><span>6-MONTH STUDY · THROUGH {data.index[-1]:%d %b %Y}</span></div>')
    metric_cards([('Window return',f'{stats["return"]:+.2f}%','Across the displayed 126 sessions'),('Annualized volatility',f'{stats["volatility"]:.1f}%','Daily return variability × √252'),('Maximum drawdown',f'{stats["drawdown"]:.2f}%','Largest decline from a window peak'),('Latest volume',compact(stats['volume']),'Reported shares · latest session')])
    left,right=st.columns([2.35,1],gap='medium')
    with left:
        with st.container(key='dark-chart'):
            panel_header(featured,COMPANIES.get(featured,featured),data)
            plot(chart(data,height=280,overlays=['SMA 20']),key='home_chart')
            html(f'<p class="source-note">HISTORICAL STUDY · {data.tail(126).index[0]:%d %b %Y} — {data.index[-1]:%d %b %Y} · Daily closes & 20-day average · Forecast shown separately</p>')
    with right:
        with st.container(key='forecast'):
            html('<div class="forecast-label"><div class="eyebrow">YOUR TRAINED MODEL / EXPERIMENTAL</div><h3>A pattern.<br>Not a promise.</h3></div>')
            if prediction is not None:
                change=(prediction/float(data.Close.iloc[-1])-1)*100
                html(f'<div class="forecast-metric">{money(prediction,featured)}</div><div class="forecast-caption">{change:+.2f}% FROM THE LAST CLOSE</div>')
            else:html('<div class="forecast-caption">Explore the price history below.</div>')
            html(f'<div class="signal-row"><span>Momentum / RSI</span><strong>{data.RSI.iloc[-1]:.1f}</strong></div><div class="signal-row"><span>20-day trend</span><strong>{"Above average" if data.Close.iloc[-1]>data.SMA_20.iloc[-1] else "Below average"}</strong></div><div class="forecast-foot">Next-session estimate after {data.index[-1]:%d %b %Y}. The original training scaler is missing. Rolling diagnostic results are available in Data & model.<a class="forecast-link" href="/Analyzer" target="_self">Inspect the model & signals ↗</a></div>')
    quotes=[]
    for symbol in symbols[:6]:
        d=get_data(symbol);close=float(d.Close.iloc[-1]);change=(close/float(d.Close.iloc[-2])-1)*100
        quotes.append(f'<a href="/Analyzer?ticker={escape(symbol)}" target="_self" class="quote-item"><div class="name">{escape(symbol)}<span>↗</span></div>{sparkline(d)}<div class="price">{money(close,symbol)}</div><div class="change {"negative" if change<0 else ""}">{change:+.2f}% <small>last session</small></div></a>')
    html('<div class="quote-strip">'+''.join(quotes)+'</div>')
    html('<p class="source-note paper" style="margin-top:9px;">SAVED HISTORICAL EXAMPLES · These are dated observations, not a live ticker.</p>')
else:
    html('<div class="no-data">The market study is being prepared. Open the analyzer to explore a stock with live data.</div>')

section('01 / THE MARKET BRIEF','The stories behind the signals.','Earnings, policy, and economic developments worth a closer look. Follow the reporting to form your own view.')
with st.spinner('Opening the latest market headlines…'):
    brief=get_brief()
topics=['All developments']+list(dict.fromkeys(a['category'] for a in brief['articles']))
topic=st.pills('News focus',topics,default='All developments',label_visibility='collapsed',key='home_news_focus')
filtered=dict(brief,articles=[a for a in brief['articles'] if topic in (None,'All developments') or a['category']==topic])
render_brief(filtered)
section('02 / THE APPROACH','A little context goes a long way.','Three ways to look at the same market. One place to put them together.')
html('''<div class="principles"><article class="principle"><span class="num">01 / OBSERVE</span><h3>Follow the pattern.</h3><p>Price, volume, and technical indicators. Begin with what the market has actually done, then inspect your model’s experimental estimate.</p></article><article class="principle"><span class="num">02 / QUESTION</span><h3>Make room for uncertainty.</h3><p>Drawdown and volatility put a move in context. Explore historical-return simulations to see how a range of paths could unfold.</p></article><article class="principle"><span class="num">03 / CONNECT</span><h3>Read beyond the chart.</h3><p>Earnings, policy, and economic developments deserve a closer look. Follow each source and compare stocks on shared trading dates.</p></article></div><div class="bottom-cta"><div class="eyebrow">YOUR RESEARCH STARTS HERE</div><h2>One ticker. A more considered view.</h2><a href="/Analyzer" target="_self">Open the studio &nbsp; ↗</a></div>''')
with st.expander('About this research project'):
    st.write('Market Navigator is Aditya’s independently trained stock prediction project. Its existing Streamlit app, model, technical indicators, and sentiment workflow have been brought into one consistent visual system.')
    st.write('The forecast is experimental. Rolling diagnostics compare the current pipeline with a last-close baseline. Original training data and the saved scaler were not recovered, so independent accuracy and calibrated probabilities remain unverified.')
footer()
