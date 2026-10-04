"""A personal session watchlist with date-aligned stock comparisons."""
from html import escape
from urllib.parse import quote
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from ui import shell,heading,html,footer,money,section,chart,plot,panel_header,sparkline,metric_cards,style_figure,workspace_navigation
from market import snapshot_symbols,get_data,predict,claim_request,COMPANIES
from research import shortlist,add_symbol,save_shortlist,aligned_prices,PERIODS

def focus_board():st.session_state['board_tab']='Compare paths'

shell('Watchlist')
html('<div class="workspace-label">02 / WATCHLIST <span>YOUR SHORTLIST · SHARED PERSPECTIVE</span></div>')
symbols=shortlist();saved_symbols=snapshot_symbols()
with st.container(key='controls'):
    a,b,c,d=st.columns([1,1.1,1.1,1.3],vertical_alignment='bottom')
    with a:region=st.selectbox('MARKET',['All markets','United States','India'])
    with b:sort=st.selectbox('SORT BY',['Symbol','Last-session change','Model estimate change'])
    with c:source=st.selectbox('PRICE SOURCE',['Saved studies','Live market data'])
    with d:run=st.button('Compare model estimates  ↗',key='compare_models',type='primary',width='stretch')
    st.caption('Model comparisons run on request. Live quotes are loaded separately; saved examples keep their original dates.')
selected=[s for s in symbols if region=='All markets' or (s.endswith(('.NS','.BO')) if region=='India' else not s.endswith(('.NS','.BO')))]
frames={}
if source=='Saved studies':frames={s:get_data(s) for s in selected if s in saved_symbols}
else:
    if st.button('Load live watchlist prices  ↗',key='load_watchlist',type='primary'):
        try:
            claim_request();loaded={};errors=[]
            with st.spinner('Reading the watchlist…'):
                for s in selected[:8]:
                    try:loaded[s]=get_data(s,'Live market data')
                    except Exception:errors.append(s)
            st.session_state['board_live']={'frames':loaded,'errors':errors}
        except ValueError as exc:st.warning(str(exc))
    live=st.session_state.get('board_live',{})
    frames={s:data for s,data in live.get('frames',{}).items() if s in selected}
    if live.get('errors'):st.caption('Unavailable on the last request: '+', '.join(live['errors'])+'. Other completed quotes remain visible.')

estimate_key=source
if run:
    try:
        if not frames:raise ValueError('Load prices before comparing the model estimates.')
        claim_request();estimates={}
        with st.spinner('Comparing the model estimates…'):
            for s,data in frames.items():estimates[s]={'date':data.index[-1].isoformat(),'close':float(data.Close.iloc[-1]),'change':(predict(data)/float(data.Close.iloc[-1])-1)*100}
        st.session_state['board_models']={'source':estimate_key,'results':estimates}
        st.session_state['board_estimates']={s:r['change'] for s,r in estimates.items()}
    except Exception as exc:st.error(str(exc) if isinstance(exc,ValueError) else 'The model comparison is temporarily unavailable.')
models=st.session_state.get('board_models',{})
estimates=models.get('results',{}) if models.get('source')==source else {}
rows=[]
for symbol in selected:
    data=frames.get(symbol);estimate=None
    if data is not None:
        previous=estimates.get(symbol,{})
        if previous.get('date')==data.index[-1].isoformat() and previous.get('close')==float(data.Close.iloc[-1]):estimate=previous['change']
    rows.append({'symbol':symbol,'name':COMPANIES.get(symbol,symbol),'data':data,'estimate':estimate,
                 'change':(float(data.Close.iloc[-1])/float(data.Close.iloc[-2])-1)*100 if data is not None else None})
if sort=='Last-session change':rows.sort(key=lambda r:r['change'] if r['change'] is not None else -float('inf'),reverse=True)
elif sort=='Model estimate change':
    rows.sort(key=lambda r:r['estimate'] if r['estimate'] is not None else -float('inf'),reverse=True)
    if not estimates:st.caption('Run the comparison to sort by model estimate change.')
valid=[r for r in rows if r['data'] is not None]
if valid:
    best=max(valid,key=lambda r:r['change']);weakest=min(valid,key=lambda r:r['change'])
    metric_cards([('On your radar',f'{len(symbols):02d} symbols','Eight-symbol session limit'),('Ready to compare',f'{len(valid):02d} studies',source),('Strongest last session',best['symbol'],f'{best["change"]:+.2f}% · dated observations'),('Weakest last session',weakest['symbol'],f'{weakest["change"]:+.2f}% · dated observations')])
board_tabs=st.tabs(['Shortlist','Compare paths'],default=st.session_state.get('board_tab','Shortlist'))
with board_tabs[0]:
    with st.expander('Edit your watchlist'):
        st.caption('Bookmark this page to keep your shortlist. Additions use live data unless a saved history is available.')
        with st.form('add_watchlist',clear_on_submit=True):
            a,b=st.columns([3,1],vertical_alignment='bottom')
            with a:new_symbol=st.text_input('ADD A TICKER',placeholder='MSFT or INFY.NS',max_chars=15)
            with b:add=st.form_submit_button('Add symbol ↗',width='stretch')
            if add:
                try:add_symbol(new_symbol);st.rerun()
                except ValueError as exc:st.warning(str(exc))
        if symbols:
            remove=st.selectbox('REMOVE A TICKER',symbols)
            if st.button('Remove selected',key='remove_symbol'):
                save_shortlist([s for s in symbols if s!=remove]);st.rerun()
    
    st.caption('Daily observations · each stock retains its source date · trends show the last 36 sessions.')
    if rows:
        table=[]
        for r in rows:
            symbol=r['symbol'];data=r['data'];estimate='Not run' if r['estimate'] is None else f'{r["estimate"]:+.2f}%'
            price=money(float(data.Close.iloc[-1]),symbol,data.attrs.get('currency')) if data is not None else '—'
            change=f'{r["change"]:+.2f}%' if r['change'] is not None else '—'
            date=data.index[-1].strftime('%d %b %Y') if data is not None else 'Load live data' if source=='Live market data' else 'Live study available'
            study_source='live' if source=='Live market data' or symbol not in saved_symbols else 'saved'
            table.append(f'<tr><td><div class="symbol">{escape(symbol)}</div><div class="company">{escape(r["name"])}</div></td><td class="trend-cell optional">{sparkline(data) if data is not None else "—"}</td><td class="mono">{price}</td><td class="mono session {"negative" if r["change"] is not None and r["change"]<0 else "positive"}">{change}</td><td class="mono optional">{estimate}</td><td><a class="view" href="/Analyzer?ticker={quote(symbol)}&amp;source={study_source}" target="_self">Study ↗</a><div class="company">{date}</div></td></tr>')
        html('<table class="screen-table"><thead><tr><th>Company / ticker</th><th class="optional">Trend</th><th>Last close</th><th class="session">Session Δ</th><th class="optional">Model Δ</th><th>Explore</th></tr></thead><tbody>'+''.join(table)+'</tbody></table>')
    else:st.info('Your shortlist is empty for this market. Add a ticker above or select another market.')
    
with board_tabs[1]:
    if len(frames)>=2:
        st.caption('Local-currency returns rebased to 100 on a shared date.')
        a,b=st.columns([2,1])
        with a:compare=st.multiselect('STOCKS TO COMPARE',list(frames),default=list(frames)[:3],max_selections=6,on_change=focus_board)
        with b:period=st.selectbox('COMPARISON WINDOW',list(PERIODS),index=2,on_change=focus_board)
        if len(compare)>=2:
            try:
                prices,rebased=aligned_prices({s:frames[s] for s in compare},PERIODS[period])
                tabs=st.tabs(['Relative performance','Return correlation'])
                with tabs[0]:
                    colors=['#193c32','#af875f','#7899a1','#7e9268','#b47060','#817996'];fig=go.Figure()
                    for (symbol,series),color in zip(rebased.items(),colors):fig.add_trace(go.Scatter(x=rebased.index,y=series,name=symbol,line=dict(color=color,width=2),hovertemplate='%{x|%d %b %Y}<br>Indexed close: %{y:.2f}<extra>'+symbol+'</extra>'))
                    fig.add_hline(y=100,line_dash='dot',line_color='#b4b9ab')
                    plot(style_figure(fig,330),key='relative_performance')
                    st.caption(f'{len(prices)} shared dates · {prices.index[0]:%d %b %Y} — {prices.index[-1]:%d %b %Y}. Base 100. Exchange holidays reduce the shared sample; currency effects are omitted.')
                    st.download_button('Download the aligned comparison ↓',rebased.rename_axis('Date').to_csv().encode(),'northstar-comparison.csv','text/csv')
                with tabs[1]:
                    returns=prices.pct_change().dropna()
                    if len(returns)<30:st.info('At least 30 shared daily returns are needed to show a correlation matrix.')
                    else:
                        matrix=returns.corr()
                        fig=go.Figure(go.Heatmap(z=matrix.to_numpy(),x=matrix.columns,y=matrix.index,zmin=-1,zmax=1,colorscale=[[0,'#c29883'],[.5,'#f5f4ee'],[1,'#39755d']],text=matrix.round(2).to_numpy(),texttemplate='%{text}',hovertemplate='%{x} / %{y}<br>Correlation: %{z:.2f}<extra></extra>',showscale=False))
                        fig.update_layout(height=320,margin=dict(l=0,r=0,t=15,b=0),paper_bgcolor='rgba(0,0,0,0)',font=dict(family='DM Mono',color='#737970',size=11))
                        plot(fig,key='correlation_matrix')
                        st.caption(f'Pearson correlation of {len(returns)} shared daily percentage returns. −1 to +1; historical association does not establish causality. A constant series has no defined correlation.')
            except ValueError as exc:st.info(str(exc))
        else:st.caption('Select at least two stocks to compare their paths.')
    elif source=='Live market data':st.caption('Load at least two stocks to open the comparison charts.')
workspace_navigation()
footer()
