"""One visual language for the public overview and research workspace."""
from pathlib import Path
from html import escape,unescape
from base64 import b64encode
from urllib.parse import urlsplit,urlunsplit,parse_qsl,urlencode
import re
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

def workspace_navigation():
    """Keep an explicitly selected view in sight after a long table or chart."""
    import streamlit.components.v1 as components
    components.html('''<script>
    const doc = window.parent.document;
    const main = doc.querySelector('[data-testid="stMain"]');
    const handler = event => {
      const tab = event.target.closest('[role="tab"]');
      if (!tab || (event.type === 'keyup' && !['ArrowLeft','ArrowRight','Home','End','Enter',' '].includes(event.key))) return;
      const list = tab.closest('[role="tablist"]');
      requestAnimationFrame(() => {
        if (main && list) main.scrollTo({top: Math.max(0, main.scrollTop + list.getBoundingClientRect().top - 20), behavior: 'instant'});
      });
    };
    const previous = doc.__northstarTabHandler;
    if (previous) { doc.removeEventListener('click', previous); doc.removeEventListener('keyup', previous); }
    doc.__northstarTabHandler = handler;
    doc.addEventListener('click', handler);
    doc.addEventListener('keyup', handler);
    </script>''',height=0)

ROOT=Path(__file__).resolve().parent
INK='#193c32';MUTED='#737970';LIME='#d5f475'

def html(content):
    def preserve_watchlist(match):
        from research import shortlist
        parts=urlsplit(unescape(match.group(1)))
        params=dict(parse_qsl(parts.query));params['watch']=','.join(shortlist())
        target=urlunsplit(('', '', parts.path,urlencode(params),parts.fragment))
        return f'href="{escape(target,quote=True)}"'
    # Ordinary HTML navigation reloads Streamlit sessions. Carry the public ticker
    # shortlist across internal links, also making the watchlist bookmarkable.
    content=re.sub(r'href="(/[^\"]*)"',preserve_watchlist,content)
    if 'href="/' in content:
        # Our escaped navigation markup needs a normal top-level anchor on
        # Community Cloud. st.html strips that target and nests hosting frames.
        st.markdown(content.replace('target="_self"','target="_top"'),unsafe_allow_html=True)
    else:
        st.html(content)

def shell(active='Overview'):
    st.set_page_config(page_title=f'Northstar — {active}',page_icon='✳',layout='wide')
    html(f'<style>{(ROOT/"assets/style.css").read_text(encoding="utf-8")}</style>')
    if active!='Overview':html('<style>.site-header{min-height:76px}.stMainBlockContainer{padding-top:0}'+(ROOT/'assets/workspace.css').read_text(encoding='utf-8')+'</style>')
    links=[('Overview','/'),('Research studio','/Analyzer'),('Watchlist','/Dashboard')]
    nav=''.join(f'<a href="{url}" target="_self" class="{"active" if name==active else ""}" {"aria-current=page" if name==active else ""}>{name}</a>' for name,url in links)
    html(f'''<header class="site-header"><a href="/" target="_self" class="wordmark"><span class="brand-index" aria-hidden="true">✳</span><span>northstar<small>MARKET NAVIGATOR</small></span></a><nav class="nav-links" aria-label="Main navigation">{nav}</nav><span class="header-note">INDEPENDENT RESEARCH<br>ADITYA GHOLAP / NOIRPRIMORDIAL7</span></header>''')

def footer():
    html('''<footer class="footer"><div><strong>Find your bearings.</strong>© 2026 Aditya Gholap · NoirPrimordial7 · <a href="https://github.com/NoirPrimordial7/AI-Powered-Market-Navigator" target="_blank" rel="noopener noreferrer">Code, training & results ↗</a></div><div class="legal">Independent research. Experimental estimates, historical simulations, and publisher headlines serve different purposes. Quotes may be delayed.</div></footer>''')
    workspace_navigation()

def section(number,title,description=''):
    html(f'<div class="section-intro"><div><div class="eyebrow">{escape(number)}</div><h2>{escape(title)}</h2></div><p>{escape(description)}</p></div>')

def heading(kicker,title,description):
    html(f'<div class="page-heading"><div class="eyebrow"><span class="status-dot"></span>{escape(kicker)}</div><h1>{title}</h1><p>{escape(description)}</p></div>')

def money(value,ticker='AAPL',currency=None):
    currency=currency or ('INR' if ticker.endswith(('.NS','.BO')) else 'USD')
    prefix={'USD':'$','INR':'₹','EUR':'€','GBP':'£','JPY':'¥','GBp':'GBp '}.get(currency,escape(currency)+' ')
    return f'{prefix}{value:,.2f}'

def compact(value):
    return f'{value/1e9:.2f}B' if value>=1e9 else f'{value/1e6:.2f}M' if value>=1e6 else f'{value:,.0f}'

def sparkline(data,width=120,height=32):
    values=data.Close.tail(36).to_numpy(dtype=float)
    if not len(values) or not np.isfinite(values).all():return ''
    span=max(float(np.ptp(values)),.00001)
    points=' '.join(f'{2+i*(width-4)/max(1,len(values)-1):.1f},{height-3-(v-values.min())/span*(height-6):.1f}' for i,v in enumerate(values))
    color='#527547' if values[-1]>=values[0] else '#a66a57'
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}"><polyline points="{points}" fill="none" stroke="{color}" stroke-width="1.5" vector-effect="non-scaling-stroke"/></svg>'
    # Streamlit's HTML sanitizer strips inline SVG elements; image sources survive.
    encoded=b64encode(svg.encode()).decode()
    return f'<img class="sparkline" src="data:image/svg+xml;base64,{encoded}" alt="Closing price trend over the last {len(values)} sessions" width="{width}" height="{height}">'

def chart(data,prediction=None,dark=True,mode='Price',days=126,height=310,overlays=None):
    view=data.tail(days);close=view.Close
    fg,grid=('#a8b6ad','rgba(255,255,255,0.06)') if dark else (MUTED,'rgba(28,37,32,0.08)')
    fig=go.Figure()
    if mode=='Candles':
        fig.add_trace(go.Candlestick(x=view.index,open=view.Open,high=view.High,low=view.Low,close=close,name='OHLC',increasing_line_color='#bcd878',decreasing_line_color='#c98d78'))
    else:
        fig.add_trace(go.Scatter(x=view.index,y=close,mode='lines',line=dict(color=LIME if dark else INK,width=2),fill='tozeroy',fillcolor='rgba(161,194,112,0.06)',name='Close',hovertemplate='%{x|%d %b %Y}<br>Close: %{y:,.2f}<extra></extra>'))
    overlays=overlays or (['SMA 20'] if mode=='Moving average' else [])
    range_values=[view.Low,view.High] if mode=='Candles' else [close]
    for label,column,color in [('SMA 20','SMA_20','#d8b899'),('SMA 50','SMA_50','#8eb6bd'),('Bollinger bands','BB_upper','#8da591'),('Bollinger bands','BB_lower','#8da591')]:
        if label in overlays:
            fig.add_trace(go.Scatter(x=view.index,y=view[column],name=column.replace('_',' '),line=dict(color=color,width=1,dash='dot')))
            range_values.append(view[column].dropna())
    if prediction is not None:
        next_day=view.index[-1]+pd.offsets.BDay(1)
        fig.add_trace(go.Scatter(x=[view.index[-1],next_day],y=[close.iloc[-1],prediction],mode='lines+markers',line=dict(color='#eec2a0',width=2,dash='dot'),marker=dict(size=[4,8]),name='Experimental model',hovertemplate='Model estimate: %{y:,.2f}<extra></extra>'))
    low=min(float(v.min()) for v in range_values if len(v));high=max(float(v.max()) for v in range_values if len(v))
    if prediction is not None:low=min(low,prediction);high=max(high,prediction)
    pad=max((high-low)*.13,high*.005)
    fig.update_layout(height=height,margin=dict(l=22,r=44,t=30,b=22),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font=dict(family='DM Mono,monospace',color=fg,size=10),showlegend=bool(overlays),legend=dict(orientation='h',y=1.15,font=dict(size=9)),hovermode='x unified',hoverlabel=dict(bgcolor='#f5f4ee',font_color='#1c2520',font_family='DM Mono'),xaxis=dict(showgrid=False,zeroline=False,tickformat='%b %d',nticks=5,rangeslider_visible=False,automargin=True),yaxis=dict(side='right',gridcolor=grid,zeroline=False,range=[low-pad,high+pad],nticks=5,tickformat=',.0f',automargin=True),dragmode=False)
    return fig

def style_figure(fig,height=230):
    fig.update_layout(height=height,margin=dict(l=8,r=30,t=28,b=22),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font=dict(family='DM Mono,monospace',color=MUTED,size=10),hovermode='x unified',legend=dict(orientation='h',y=1.2,font=dict(size=10)),xaxis=dict(showgrid=False,nticks=5,automargin=True),yaxis=dict(side='right',gridcolor='#e0e3d8',zeroline=False,automargin=True),dragmode=False)
    return fig

def volume_chart(data,days=126):
    view=data.tail(days)
    fig=go.Figure(go.Bar(x=view.index,y=view.Volume,marker_color=np.where(view.Close>=view.Open,'#b4c6a6','#d4b4a4'),hovertemplate='%{x|%d %b}<br>%{y:,.0f} shares<extra></extra>'))
    return style_figure(fig,125)

def signal_chart(data,signal,days=126):
    view=data.tail(days);fig=go.Figure()
    if signal=='RSI':
        fig.add_trace(go.Scatter(x=view.index,y=view.RSI,name='RSI 14',line=dict(color=INK,width=2)))
        for level in [30,70]:fig.add_hline(y=level,line_dash='dot',line_color='#b69573')
        fig.update_yaxes(range=[0,100]);fig.update_layout(showlegend=False)
    elif signal=='MACD':
        diff=view.MACD-view.MACD_signal
        fig.add_trace(go.Bar(x=view.index,y=diff,name='Difference',marker_color=np.where(diff>=0,'#c0d2b1','#d8bbad')))
        for label,column,color in [('MACD','MACD',INK),('Signal','MACD_signal','#b48760')]:
            fig.add_trace(go.Scatter(x=view.index,y=view[column],name=label,line=dict(color=color,width=1.5)))
    else:
        drawdown=(view.Close/view.Close.cummax()-1)*100
        fig.add_trace(go.Scatter(x=view.index,y=drawdown,name='Drawdown',fill='tozeroy',line=dict(color='#a66a57',width=1.7),fillcolor='rgba(166,106,87,.10)'))
        fig.update_layout(showlegend=False);fig.update_yaxes(ticksuffix='%')
    return style_figure(fig)

def scenario_chart(paths):
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=paths.index,y=paths['Upper 90%'],name='Upper 90%',line=dict(width=0),hovertemplate='%{y:,.2f}<extra>Upper 90%</extra>'))
    fig.add_trace(go.Scatter(x=paths.index,y=paths['Lower 10%'],name='Lower 10%',line=dict(width=0),fill='tonexty',fillcolor='rgba(145,171,113,.22)',hovertemplate='%{y:,.2f}<extra>Lower 10%</extra>'))
    fig.add_trace(go.Scatter(x=paths.index,y=paths.Median,name='Median',line=dict(color=INK,width=2)))
    return style_figure(fig,310)

def plot(fig,key):st.plotly_chart(fig,use_container_width=True,theme=None,config={'displayModeBar':False,'scrollZoom':False},key=key)

def panel_header(ticker,name,data,badge='Historical snapshot'):
    price=float(data.Close.iloc[-1]);change=(price/float(data.Close.iloc[-2])-1)*100
    html(f'<div class="panel-head"><div><div class="dark-label">PRICE PERFORMANCE / {escape(ticker)}</div><div class="panel-title">{escape(name)}<span>{escape(ticker)}</span></div><div class="panel-price">{money(price,ticker,data.attrs.get("currency"))}<small class="{"negative" if change<0 else ""}">{change:+.2f}% &nbsp; last session</small></div></div><span class="tag">{escape(badge)}</span></div>')

def metric_cards(rows):
    html('<div class="metric-grid cards">'+''.join(f'<div class="metric-block"><div class="label">{escape(label)}</div><div class="value">{escape(str(value))}</div><div class="sub">{escape(note)}</div></div>' for label,value,note in rows)+'</div>')

def metrics(data,prediction,ticker):
    current=float(data.Close.iloc[-1]);currency=data.attrs.get('currency')
    metric_cards([('Last close',money(current,ticker,currency),data.index[-1].strftime('%d %b %Y')),('Model estimate',money(prediction,ticker,currency),'Experimental · next session'),('Estimated change',f'{(prediction/current-1)*100:+.2f}%','Relative to the last close'),('Momentum / RSI',f'{data.RSI.iloc[-1]:.1f}','14-session relative strength')])
