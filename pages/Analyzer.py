"""A focused research desk with prices, risk, scenarios, and source-linked news."""
from html import escape
import json
from pathlib import Path
import pandas as pd
import streamlit as st
from ui import shell,html,footer,heading,metric_cards,chart,plot,panel_header,money,compact,volume_chart,signal_chart,scenario_chart,workspace_navigation
from market import analyze,get_data,predict,snapshot_symbols,validate_ticker,claim_request,sentiments,secret,COMPANIES
from news import get_brief,render_brief
from research import PERIODS,summary,scenario_paths,read_prices,shortlist

def focus_tab(name):st.session_state['research_tab']=name

shell('Research studio')
html('<div class="workspace-label">01 / RESEARCH STUDIO <span>PRICE · SIGNALS · CONTEXT</span></div>')
symbols=snapshot_symbols();incoming=str(st.query_params.get('ticker','')).upper()
incoming_source='Live market data' if st.query_params.get('source')=='live' else 'Historical example'
query_identity=(incoming,incoming_source)
if incoming and query_identity!=st.session_state.get('opened_query'):
    st.session_state['opened_query']=query_identity
    try:
        incoming=validate_ticker(incoming)
        st.session_state['research_ticker']=incoming
        st.session_state['research_source']=incoming_source if incoming in symbols else 'Live market data'
        if incoming in symbols or incoming_source=='Live market data':
            claim_request();data,estimate=analyze(incoming,incoming_source)
            st.session_state['study']={'ticker':incoming,'source':incoming_source,'data':data,'prediction':estimate}
            focus_tab('Price & activity')
    except Exception as exc:st.warning(str(exc) if isinstance(exc,ValueError) else 'This linked study is temporarily unavailable. Your last completed study remains below.')
if 'study' not in st.session_state and symbols:
    data,estimate=analyze('AAPL' if 'AAPL' in symbols else symbols[0],'Historical example')
    st.session_state['study']={'ticker':'AAPL' if 'AAPL' in symbols else symbols[0],'source':'Historical example','data':data,'prediction':estimate}

with st.container(key='study-controls'):
    with st.expander('Change stock, data source or upload a CSV',expanded=False):
        unknown_query=bool(incoming and incoming not in symbols)
        source=st.selectbox('DATA SOURCE',['Historical example','Live market data','Upload CSV'],index=1 if unknown_query else 0,key='research_source')
        uploaded=None;upload_currency=None
        if source=='Upload CSV':
            uploaded=st.file_uploader('PRICE HISTORY',type='csv',help='Date, Open, High, Low, Close, Volume. At least 60 daily rows. Maximum 5 MB.')
            upload_currency=st.selectbox('QUOTE CURRENCY',['USD','INR','EUR','GBP','JPY'])
        default=incoming or st.session_state.get('study',{}).get('ticker','AAPL')
        with st.form('analysis_form'):
            ticker=st.text_input('STOCK TICKER',value=default,placeholder='AAPL or RELIANCE.NS',max_chars=15,key='research_ticker')
            submitted=st.form_submit_button('Open study  ↗',type='primary',width='stretch')
        st.caption('Saved histories open without API keys. Live requests cache for 15 minutes.')
        if submitted:
            try:
                ticker=validate_ticker(ticker);claim_request()
                with st.spinner('Preparing your study…'):
                    if source=='Upload CSV':
                        if uploaded is None:raise ValueError('Choose a CSV to open this study.')
                        data=read_prices(uploaded.getvalue());data.attrs['currency']=upload_currency
                        estimate=predict(data)
                    else:data,estimate=analyze(ticker,source)
                st.session_state['study']={'ticker':ticker,'source':'Uploaded CSV' if source=='Upload CSV' else source,'data':data,'prediction':estimate}
                focus_tab('Price & activity')
            except Exception as exc:
                st.error(str(exc) if isinstance(exc,ValueError) else 'This study is temporarily unavailable. Try a saved history or another ticker.')
                st.caption('Your previous completed study remains on the desk.')
        html('<div class="quick-radar">'+''.join(f'<a href="/Analyzer?ticker={escape(symbol)}&amp;source={"saved" if symbol in symbols else "live"}" target="_self">{escape(symbol)} ↗</a>' for symbol in shortlist()[:6])+'</div>')

with st.container(key='research-workspace'):
    study=st.session_state.get('study')
    if not study:st.info('Open a stock to begin your research.')
    else:
        ticker=study['ticker'];data=study['data'];prediction=study['prediction'];source=study['source'];currency=data.attrs.get('currency')
        period=st.session_state.get('study_period','6 months');days=PERIODS[period];view=data.tail(days);stats=summary(view)
        html(f'<div class="study-title"><div><div class="eyebrow">COMPLETED STUDY / {escape(ticker)}</div><h2>{escape(COMPANIES.get(ticker,ticker))}</h2></div><div class="study-date"><span>{escape(source)}</span><strong>Through {data.index[-1]:%d %b %Y}</strong></div></div>')
        metric_cards([('Window return',f'{stats["return"]:+.2f}%',f'{len(view)} trading sessions'),('Annualized volatility',f'{stats["volatility"]:.1f}%','Daily variability × √252'),('Max. drawdown',f'{stats["drawdown"]:.2f}%','Relative to a window peak'),('Latest volume',compact(stats['volume']),'Shares · latest observation')])
        names=['Price & activity','Signals & risk','Scenarios','Headlines','Data & model']
        tabs=st.tabs(names,default=st.session_state.get('research_tab',names[0]))
        with tabs[0]:
            with st.expander('Chart settings',expanded=False):
                a,b,c=st.columns([1,1,1.4])
                with a:period=st.selectbox('CHART WINDOW',list(PERIODS),index=2,key='study_period',on_change=focus_tab,args=(names[0],))
                with b:mode=st.selectbox('CHART VIEW',['Price','Candles','Moving average'],key='study_mode',on_change=focus_tab,args=(names[0],))
                with c:overlays=st.multiselect('OVERLAYS',['SMA 20','SMA 50','Bollinger bands'],default=['SMA 20'],key='study_overlays',on_change=focus_tab,args=(names[0],))
                show_estimate=st.toggle('Show experimental model estimate on the chart',value=False,key='show_estimate',on_change=focus_tab,args=(names[0],))
            days=PERIODS[period]
            with st.container(key='dark-chart'):
                panel_header(ticker,COMPANIES.get(ticker,ticker),data,source)
                plot(chart(data,prediction if show_estimate else None,mode=mode,days=days,height=230,overlays=overlays),key='study_price')
                html(f'<p class="source-note">{data.tail(days).index[0]:%d %b %Y} — {data.index[-1]:%d %b %Y} · Daily prices · Hover to inspect · {"Dotted segment: experimental model estimate" if show_estimate else "Model estimate shown separately below"}</p>')
            html('<div class="activity-label"><span>TRADING ACTIVITY</span><span>REPORTED DAILY VOLUME</span></div>')
            plot(volume_chart(data,days),key='study_volume')
            left,right=st.columns([1.15,1],gap='medium')
            with left:
                html(f'<aside class="model-panel"><div class="eyebrow">YOUR TRAINED MODEL / EXPERIMENTAL</div><h3>The next-session estimate.</h3><div class="model-value">{money(prediction,ticker,currency)}<span>{(prediction/float(data.Close.iloc[-1])-1)*100:+.2f}% from the last close</span></div><p>For the trading session after {data.index[-1]:%d %b %Y}. These original model weights use the app’s per-history scaling. A saved training scaler and evaluation results were not supplied.</p></aside>')
            with right:
                trend='Above' if data.Close.iloc[-1]>data.SMA_20.iloc[-1] else 'Below'
                html(f'<aside class="research-note"><div class="eyebrow">THE CURRENT PICTURE</div><h3>{trend} its recent average.</h3><p>RSI is {data.RSI.iloc[-1]:.1f}. The selected window returned {stats["return"]:+.2f}%, with a maximum drawdown of {stats["drawdown"]:.2f}%. Compare these observations with the model before forming a view.</p></aside>')
        with tabs[1]:
            html(f'<div class="tab-intro"><div class="eyebrow">{escape(ticker)} / {escape(source)}</div><h3>Look beneath the line.</h3><p>Momentum and trend measures describe the selected window. Reference levels are context, not automatic trade signals.</p></div>')
            a,b=st.columns(2)
            with a:
                st.markdown('**Relative strength / RSI 14**');plot(signal_chart(data,'RSI',days),key='rsi_chart')
                st.caption('30 and 70 are reference levels. RSI measures the balance of recent gains and losses.')
            with b:
                st.markdown('**Trend momentum / MACD**');plot(signal_chart(data,'MACD',days),key='macd_chart')
                st.caption('12- and 26-session averages, with a 9-session signal line. Bars show their difference.')
            st.markdown('**Drawdown / the selected window**');plot(signal_chart(data,'Drawdown',days),key='drawdown_chart')
            st.caption('Decline from each running closing-price peak inside this window. This matches the maximum drawdown card.')
            last=data.iloc[-1]
            rows=[('RSI / 14',f'{last.RSI:.2f}'),('SMA / 20',money(last.SMA_20,ticker,currency)),('SMA / 50',money(last.SMA_50,ticker,currency)),('MACD',f'{last.MACD:+.3f}'),('Signal',f'{last.MACD_signal:+.3f}')]
            html('<div class="signal-strip">'+''.join(f'<div><span>{label}</span><strong>{value}</strong></div>' for label,value in rows)+'</div>')
        with tabs[2]:
            html(f'<div class="tab-intro"><div class="eyebrow">{escape(ticker)} / {escape(source)}</div><h3>Make room for more than one path.</h3><p>A historical-return simulation. This is separate from your trained AI model and does not incorporate news or future business changes.</p></div>')
            horizon=st.slider('TRADING-SESSION HORIZON',5,60,20,5,key='scenario_horizon',on_change=focus_tab,args=(names[2],))
            paths=scenario_paths(data,horizon)
            plot(scenario_chart(paths),key='scenario_chart')
            a,b,c=st.columns(3)
            for col,label in zip([a,b,c],paths.columns):
                with col:st.metric(label,money(paths[label].iloc[-1],ticker,currency))
            st.caption(f'{horizon} simulated business dates after {data.index[-1]:%d %b %Y}. The band is the simulated 10th–90th percentile range, not validated forecast confidence.')
            with st.expander('How these scenarios are calculated'):
                st.write('400 deterministic paths use the mean and sample standard deviation of up to 252 historical daily log returns. The assumptions are independent normally distributed returns and constant volatility. Earnings, news, trading costs, extreme events, and exchange holidays are not modeled.')
        with tabs[3]:
            html(f'<div class="tab-intro"><div class="eyebrow">{escape(ticker)} / {escape(source)}</div><h3>The stories around the stock.</h3><p>Current publisher headlines that name this stock or company. Dates are independent of the price study; headlines do not enter the saved model.</p></div>')
            if source!='Live market data':st.caption(f'Your price study ends on {data.index[-1]:%d %B %Y}. Headlines below use their own publication dates.')
            if st.button('Load headlines  ↗',key='load_news',type='primary',on_click=focus_tab,args=(names[3],)):
                try:
                    claim_request()
                    with st.spinner('Reading current headlines…'):brief=get_brief(ticker)
                    st.session_state['news_result']={'ticker':ticker,'brief':brief}
                except ValueError as exc:st.warning(str(exc))
            saved=st.session_state.get('news_result',{})
            if saved.get('ticker')==ticker:render_brief(saved['brief'])
            else:st.caption('No API key needed. Publisher coverage varies; some Indian tickers have no recent headlines.')
            with st.expander('Optional news & Reddit sentiment'):
                connected=bool(secret('NEWS_API_KEY') or (secret('REDDIT_CLIENT_ID') and secret('REDDIT_CLIENT_SECRET')))
                if source!='Live market data':st.info('Run a live study to load current sentiment. Historical studies keep current discussion separate.')
                elif not connected:st.caption('Sentiment connections are not configured. Headlines, charts, and model inference work independently.')
                elif st.button('Load current sentiment',key='load_sentiment',on_click=focus_tab,args=(names[3],)):
                    try:
                        claim_request();st.session_state['sentiment_result']={'ticker':ticker,'scores':sentiments(ticker)}
                    except ValueError as exc:st.warning(str(exc))
                saved_sentiment=st.session_state.get('sentiment_result',{})
                if source=='Live market data' and saved_sentiment.get('ticker')==ticker:
                    if not saved_sentiment['scores']:st.info('No sentiment observations were returned.')
                    for name,result in saved_sentiment['scores'].items():
                        if 'error' in result:st.warning(result['error'])
                        else:st.metric(f'{name} · {result["count"]} observations',f'{result["score"]:+.2f}')
                    st.caption('VADER compound score from −1 to +1. This is not a price forecast.')
        with tabs[4]:
            html(f'<div class="tab-intro"><div class="eyebrow">{escape(ticker)} / {escape(source)}</div><h3>Know what sits behind every number.</h3><p>Your original model is preserved. Its required input is 30 sessions × 11 features; the app uses the latest 30 rows in the original feature order.</p></div>')
            st.write('The model combines a bidirectional LSTM, GRU, and LSTM, with dropout and one price output. The original per-history MinMax scaling is retained. Without its saved training scaler and evaluation dataset, prediction accuracy and calibration cannot be verified. No confidence score is invented.')
            st.caption('Model features: Open, High, Low, Close, Volume, RSI, SMA 20, MACD, MACD signal, and upper/lower Bollinger Bands. Additional displayed indicators are not added to its input.')
            report_path=Path(__file__).resolve().parents[1]/'evaluation'/'metrics.json'
            if report_path.exists():
                report=json.loads(report_path.read_text(encoding='utf-8'))
                st.markdown('**Measured pipeline diagnostic · 378 next-session predictions**')
                st.caption('Expanding-history evaluation, 63 targets per saved symbol. Original training overlap is unknown; these are not verified independent holdout or original training scores.')
                results=[{'Symbol':r['symbol'],'Model MAPE %':round(r['model']['mape_percent'],2),'Last-close baseline MAPE %':round(r['persistence']['mape_percent'],2),'Direction correct %':round(r['model']['directional_accuracy_percent'],2),'Targets':r['model']['n']} for r in report['results']]
                st.dataframe(pd.DataFrame(results),hide_index=True,width='stretch')
                st.write(f'Mean percentage error: model {report["macro_model_mape_percent"]:.2f}% · last-close baseline {report["macro_persistence_mape_percent"]:.2f}%. The current pipeline underperforms the baseline on every evaluated symbol. Percentage error is not a classification accuracy score.')
                st.download_button('Download evaluation report ↓',report_path.read_bytes(),'northstar-evaluation.json','application/json',on_click=focus_tab,args=(names[4],))
            html('<p class="documentation-links"><a href="https://github.com/NoirPrimordial7/AI-Powered-Market-Navigator/blob/main/docs/MODEL_CARD.md" target="_blank" rel="noopener noreferrer">Model & training documentation ↗</a> · <a href="https://github.com/NoirPrimordial7/AI-Powered-Market-Navigator/blob/main/docs/EVALUATION.md" target="_blank" rel="noopener noreferrer">Test method & complete results ↗</a></p>')
            export=data.copy();export['Symbol']=ticker;export['Source']=source;export['Currency']=currency or 'Quote units'
            st.download_button('Download this research dataset ↓',export.to_csv().encode(),file_name=f'{ticker.lower()}-{data.index[-1]:%Y%m%d}.csv',mime='text/csv',on_click=focus_tab,args=(names[4],))
            st.dataframe(data.sort_index(ascending=False),width='stretch',height=340)
            with st.expander('Reading the fields'):
                st.write('Window return: last/first close minus one. Volatility: daily-return sample standard deviation × √252. Maximum drawdown: largest closing-price decline from a running peak in the selected window. SMA: a simple closing-price average. Volume: daily reported traded shares. The forecast and scenario dates exclude weekends, but not exchange holidays.')
workspace_navigation()
footer()


