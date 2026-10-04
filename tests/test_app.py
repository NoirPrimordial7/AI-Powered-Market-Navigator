"""Regression checks for actual inference, submitted studies, and bounded work."""
import math
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path
from contextlib import closing
from unittest.mock import patch
from datetime import datetime,timezone
from streamlit.testing.v1 import AppTest
import market
import news

ROOT=Path(__file__).resolve().parents[1]

class ModelTests(unittest.TestCase):
    def test_full_history_is_adapted_to_trained_input(self):
        data=market.get_data('AAPL')
        self.assertGreater(len(data),30)
        model,_=market.model_resource()
        self.assertEqual(model.input_shape,(None,30,11))
        value=market.predict(data)
        self.assertTrue(math.isfinite(value) and value>0)

    def test_ticker_rejects_paths_and_urls(self):
        for ticker in ['../AAPL','https://example.com','AAPL<script>','']:
            with self.assertRaises(ValueError):market.validate_ticker(ticker)
        self.assertEqual(market.validate_ticker(' reliance.ns '),'RELIANCE.NS')

class InterfaceTests(unittest.TestCase):
    def test_pages_render(self):
        for name in ['app.py','pages/Analyzer.py','pages/Dashboard.py']:
            with self.subTest(name=name):
                with patch.object(news,'get_brief',return_value={'articles':[],'checked':datetime(2026,10,4,tzinfo=timezone.utc),'unavailable':[]}):
                    app=AppTest.from_file(str(ROOT/name),default_timeout=40).run()
                self.assertEqual(list(app.exception),[])

    def test_submit_replaces_study_and_invalid_input_retains_previous(self):
        app=AppTest.from_file(str(ROOT/'pages/Analyzer.py'),default_timeout=40).run()
        app.text_input[0].set_value('NVDA')
        app.button[0].click().run()
        self.assertEqual(app.session_state['study']['ticker'],'NVDA')
        self.assertEqual(list(app.exception),[])
        app.text_input[0].set_value('../AAPL')
        app.button[0].click().run()
        self.assertTrue(app.error)
        self.assertEqual(app.session_state['study']['ticker'],'NVDA')
        app.selectbox[2].select('Candles').run()
        self.assertEqual(list(app.exception),[])

    def test_board_only_compares_filtered_symbols(self):
        app=AppTest.from_file(str(ROOT/'pages/Dashboard.py'),default_timeout=40).run()
        app.selectbox[0].select('India').run()
        app.button[0].click().run()
        self.assertEqual(list(app.exception),[])
        self.assertEqual(set(app.session_state['board_estimates']),{'RELIANCE.NS','TCS.NS'})

class RequestLimitTests(unittest.TestCase):
    def test_global_cap_survives_new_session_identity(self):
        scratch=ROOT/'.tmp';scratch.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temp:
            self.assertTrue(Path(temp).resolve().is_relative_to(scratch.resolve()))
            with patch.object(market,'ROOT',Path(temp)),patch.object(market.st,'session_state',{}):
                market.claim_request()
                path=Path(temp)/'.cache'/'limits.sqlite'
                with closing(sqlite3.connect(path)) as db, db:
                    db.executemany('INSERT INTO requests VALUES (?,?)',[('other-visitor',time.time()) for _ in range(119)])
                market.st.session_state.clear()
                with self.assertRaisesRegex(ValueError,'hourly'):market.claim_request()

class NewsTests(unittest.TestCase):
    def test_stock_feed_excludes_unrelated_and_promotional_headlines(self):
        self.assertTrue(news.matches_ticker('Supreme Court case involving Apple','AAPL'))
        self.assertTrue(news.matches_ticker('AAPL earnings ahead','AAPL'))
        self.assertFalse(news.matches_ticker('AI Registry reports crawler requests','AAPL'))
        self.assertFalse(news.matches_ticker('Pineapple exports increase','AAPL'))
        self.assertTrue(news.matches_ticker('Tata Consultancy announces quarterly results','TCS.NS'))

    def test_feed_filters_unsafe_undated_and_stale_articles(self):
        now=datetime(2026,10,4,15,tzinfo=timezone.utc)
        items=[('Apple raises earnings guidance','https://example.com/a','Sun, 04 Oct 2026 10:00:00 GMT'),
               ('Unsafe','javascript:alert(1)','Sun, 04 Oct 2026 10:00:00 GMT'),
               ('Old news','https://example.com/b','Sun, 04 Jan 2026 10:00:00 GMT'),
               ('No date','https://example.com/c',''),
               ('Future','https://example.com/d','Mon, 05 Oct 2026 10:00:00 GMT')]
        xml='<rss><channel>'+''.join(f'<item><title>{title}</title><link>{url}</link><pubDate>{date}</pubDate></item>' for title,url,date in items)+'</channel></rss>'
        articles=news.parse_feed(xml,'Test publisher',now)
        self.assertEqual(len(articles),1)
        self.assertEqual(articles[0]['category'],'Earnings')
        self.assertEqual(articles[0]['source'],'Test publisher')

    def test_deduplication_and_recency_outweigh_old_event(self):
        now=datetime(2026,10,4,15,tzinfo=timezone.utc)
        def article(title,url,date):
            return dict(title=title,url=url,published=date,category=news.event_context(title)[0])
        recent=article('Latest market overview','https://example.com/new',now)
        older=article('Earnings guidance','https://example.com/old',datetime(2026,10,1,tzinfo=timezone.utc))
        duplicate=dict(recent,url='https://example.com/new?tracking=1')
        selected=news.select_articles([older,recent,duplicate],now)
        self.assertEqual([a['title'] for a in selected],['Latest market overview','Earnings guidance'])

    def test_partial_outage_preserves_other_feed_and_cached_result(self):
        news.get_brief.clear()
        article={'title':'Fed rate cut','url':'https://example.com/a','published':datetime.now(timezone.utc),'category':'Rates & inflation','context':'Rates context'}
        def fetch(feed):
            return ([],feed[0]) if feed[0]=='CNBC' else ([article],None)
        with patch.object(news,'fetch_feed',side_effect=fetch) as mocked:
            result=news.get_brief()
            self.assertEqual(result['unavailable'],['CNBC'])
            self.assertEqual(result['articles'],[article])
            news.get_brief()
            self.assertEqual(mocked.call_count,2)
        news.get_brief.clear()

    def test_headlines_load_for_completed_ticker_only(self):
        brief={'articles':[],'checked':datetime.now(timezone.utc),'unavailable':[]}
        with patch.object(news,'get_brief',return_value=brief) as fetch:
            app=AppTest.from_file(str(ROOT/'pages/Analyzer.py'),default_timeout=40).run()
            self.assertEqual(fetch.call_count,0)
            app.button(key='load_news').click().run()
            fetch.assert_called_once_with('AAPL')
            self.assertEqual(app.session_state['news_result']['ticker'],'AAPL')
            self.assertEqual(list(app.exception),[])

if __name__=='__main__':unittest.main()
