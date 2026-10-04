"""A bounded, key-free headline brief. Editorial context never enters inference."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import escape, unescape
import re
from urllib.parse import urlsplit, urlencode, urlunsplit
import xml.etree.ElementTree as ET
import requests
import streamlit as st
from market import validate_ticker

UTC=timezone.utc
FEEDS=[('CNBC','https://www.cnbc.com/id/10000664/device/rss/rss.html'),
       ('Federal Reserve','https://www.federalreserve.gov/feeds/press_monetary.xml')]
NEWS_NAMES={'AAPL':['Apple','iPhone'],'MSFT':['Microsoft'],'NVDA':['Nvidia'],
            'GOOGL':['Alphabet','Google'],'GOOG':['Alphabet','Google'],'AMZN':['Amazon'],
            'META':['Meta','Facebook','Instagram'],'TSLA':['Tesla'],'SPY':['S&P 500','SPDR'],
            'RELIANCE.NS':['Reliance'],'TCS.NS':['Tata Consultancy','TCS'],
            'INFY.NS':['Infosys'],'HDFCBANK.NS':['HDFC']}
# These explanations describe the event category, not this article's price impact.
TOPICS=[('Earnings',r'\b(earnings|profit|profits|revenue|guidance|quarterly results)\b',
         'Watch for changes in profit expectations and forward guidance.'),
        ('Rates & inflation',r'\b(fed|fomc|interest rates?|rate (cut|hike)|inflation|cpi|monetary policy)\b',
         'Rates and inflation can change borrowing costs and company valuations.'),
        ('Deals & capital',r'\b(merger|acquisition|acquires?|takeover|buyout|ipo|buyback)\b',
         'A deal or capital decision can change ownership, funding, or shareholder returns.'),
        ('Policy & risk',r'\b(tariffs?|regulat\w*|antitrust|sanctions?|supreme court|lawsuit|war|export ban|election)\b',
         'Policy and legal developments can change costs or access to markets.'),
        ('Economic data',r'\b(jobs report|payrolls?|unemployment|gdp|recession|employment|economic growth)\b',
         'Economic releases can shift expectations for demand and interest rates.'),
        ('Business shifts',r'\b(launch\w*|chip\w*|contract|partnership|production|layoffs?)\b',
         'Business developments can change demand, capacity, or competition.')]

def event_context(title):
    for label,pattern,context in TOPICS:
        if re.search(pattern,title,re.I):return label,context
    return 'Market watch','Read the original report and compare it with the wider market context.'

def matches_ticker(title,ticker):
    # Provider ticker feeds also include loosely related and promotional stories.
    terms=[ticker]+NEWS_NAMES.get(ticker,[])
    return any(re.search(r'(?<!\w)'+re.escape(term)+r'(?!\w)',title,re.I) for term in terms)

def clean_text(value):
    return ' '.join(re.sub(r'<[^>]*>',' ',unescape(value or '')).split())[:300]

def parse_feed(content,source,now=None):
    now=now or datetime.now(UTC)
    root=ET.fromstring(content)
    articles=[]
    for item in root.findall('.//item')[:60]:
        title=clean_text(item.findtext('title'))
        link=(item.findtext('link') or '').strip()
        parts=urlsplit(link)
        if not title or parts.scheme not in ('https','http') or not parts.hostname or parts.username:continue
        try:
            published=parsedate_to_datetime(item.findtext('pubDate') or '')
            if published.tzinfo is None:published=published.replace(tzinfo=UTC)
            published=published.astimezone(UTC)
        except (TypeError,ValueError,OverflowError):continue
        # No undated, stale, or future stories presented as current.
        if not now-timedelta(days=14)<=published<=now+timedelta(minutes=5):continue
        category,context=event_context(title)
        articles.append({'title':title,'url':link,'source':source,'published':published,
                         'category':category,'context':context})
    return articles

def fetch_feed(feed):
    source,url=feed
    try:
        with requests.get(url,timeout=(3,5),stream=True,
                          headers={'User-Agent':'Mozilla/5.0 MarketNavigator/1.0'}) as response:
            response.raise_for_status()
            chunks=[];size=0
            for chunk in response.iter_content(16384):
                size+=len(chunk)
                if size>1_000_000:raise ValueError('Feed exceeded size limit')
                chunks.append(chunk)
            return parse_feed(b''.join(chunks),source),None
    except (requests.RequestException,ET.ParseError,ValueError):
        return [],source

def select_articles(articles,now=None,limit=4,diversify=False):
    now=now or datetime.now(UTC)
    # Modest event boost; recency still dominates. No fake impact score shown.
    def rank(a):
        age=max(0,(now-a['published']).total_seconds()/3600)
        return (12 if a['category']!='Market watch' else 0)-age
    seen_titles=set();seen_urls=set();selected=[]
    for article in sorted(articles,key=rank,reverse=True):
        title=re.sub(r'\W+','',article['title']).casefold()
        parts=urlsplit(article['url'])
        canonical=urlunsplit((parts.scheme,parts.netloc,parts.path,'',''))
        if title in seen_titles or canonical in seen_urls:continue
        seen_titles.add(title);seen_urls.add(canonical);selected.append(article)
    if diversify:
        topics=set();primary=[];deferred=[]
        for article in selected:
            if article['category'] in topics:deferred.append(article)
            else:topics.add(article['category']);primary.append(article)
        selected=primary+deferred
    return selected[:limit]

@st.cache_data(ttl=900,max_entries=32,show_spinner=False)
def get_brief(ticker=None):
    feeds=FEEDS
    if ticker:
        ticker=validate_ticker(ticker)
        feeds=[('Yahoo Finance','https://finance.yahoo.com/rss/headline?'+urlencode({'s':ticker}))]
    with ThreadPoolExecutor(max_workers=2) as executor:
        results=list(executor.map(fetch_feed,feeds))
    articles=[a for batch,_ in results for a in batch]
    if ticker:articles=[a for a in articles if matches_ticker(a['title'],ticker)]
    else:articles=[a for a in articles if a['category']!='Market watch']
    return {'articles':select_articles(articles,limit=12,diversify=True),'checked':datetime.now(UTC),
            'unavailable':[source for _,source in results if source]}

def render_brief(brief):
    articles=brief['articles'][:4]
    if not articles:
        st.info('No recent headlines are available from these publishers. Price analysis still works. Check back after the next feed update.')
    else:
        cards=[]
        for i,a in enumerate(articles):
            date=a['published'].strftime('%d %b %Y · %H:%M UTC')
            cards.append(f'''<article class="news-story {'news-lead' if i==0 else ''}">
                <div class="news-meta"><span>{escape(a['category'])}</span><span>{escape(a['source'])}</span></div>
                <h3><a href="{escape(a['url'],quote=True)}" target="_blank" rel="noopener noreferrer">{escape(a['title'])}<span aria-hidden="true"> ↗</span></a></h3>
                {'<p class="news-context">'+escape(a['context'])+'</p>' if i==0 else ''}
                <time datetime="{a['published'].isoformat()}">{date}</time></article>''')
        st.html(f'<div class="news-spread news-count-{len(articles)}">'+''.join(cards)+'</div>')
    st.caption(f"Feed checked {brief['checked']:%d %b %Y · %H:%M UTC}. Cached for 15 minutes. Selected by headline keywords and recency, not measured price impact.")
    if brief['unavailable']:st.caption('Temporarily unavailable: '+', '.join(brief['unavailable'])+'. '+('Other available feeds are shown.' if articles else 'Price analysis remains available.'))
