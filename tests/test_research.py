"""Financial calculations, input validation, and combined workspace interactions."""
import unittest
import numpy as np
import pandas as pd
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
import market
import research
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class ResearchTests(unittest.TestCase):
    def test_upload_sorts_dates_and_rejects_bad_ohlc_and_duplicates(self):
        frame=market.get_data('AAPL').iloc[::-1]
        loaded=research.read_prices(frame.to_csv().encode())
        self.assertTrue(loaded.index.is_monotonic_increasing)
        self.assertEqual(loaded.Close.iloc[-1],frame.Close.iloc[0])
        malformed=frame.copy();malformed.iloc[0,malformed.columns.get_loc('High')]=1
        with self.assertRaisesRegex(ValueError,'High'):research.read_prices(malformed.to_csv().encode())
        duplicate=pd.concat([frame,frame.iloc[:1]])
        with self.assertRaisesRegex(ValueError,'unique'):research.read_prices(duplicate.to_csv().encode())

    def test_risk_measures_use_selected_window(self):
        frame=pd.DataFrame({'Close':[100,120,90,108],'High':[101,121,91,109],'Low':[99,119,89,107],'Volume':[1,2,3,4]})
        stats=research.summary(frame)
        self.assertAlmostEqual(stats['return'],8)
        self.assertAlmostEqual(stats['drawdown'],-25)
        self.assertAlmostEqual(stats['volatility'],frame.Close.pct_change().dropna().std()*np.sqrt(252)*100)
        self.assertAlmostEqual(research.summary(frame.tail(2))['drawdown'],0)

    def test_scenarios_are_positive_ordered_reproducible_and_future_dated(self):
        data=market.get_data('AAPL')
        paths=research.scenario_paths(data,20)
        pd.testing.assert_frame_equal(paths,research.scenario_paths(data,20))
        self.assertEqual(len(paths),20)
        self.assertTrue((paths>0).all().all())
        self.assertTrue((paths['Lower 10%']<=paths.Median).all())
        self.assertTrue((paths.Median<=paths['Upper 90%']).all())
        self.assertGreater(paths.index[0],data.index[-1])
        with self.assertRaises(ValueError):research.scenario_paths(data,61)

    def test_comparison_uses_shared_dates_and_one_starting_point(self):
        dates=pd.date_range('2026-01-01',periods=4)
        a=pd.DataFrame({'Close':[100,110,120,125]},index=dates)
        b=pd.DataFrame({'Close':[55,60,65]},index=dates[1:])
        prices,indexed=research.aligned_prices({'A':a,'B':b})
        self.assertEqual(list(prices.index),list(dates[1:]))
        self.assertTrue((indexed.iloc[0]==100).all())
        self.assertAlmostEqual(indexed.A.iloc[-1],125/110*100)
        with self.assertRaises(ValueError):research.aligned_prices({'A':a})

    def test_watchlist_limits_and_isolation(self):
        with patch.object(market.st,'session_state',{}):
            research.add_symbol('MSFT') if 'MSFT' not in research.shortlist() else None
            with self.assertRaisesRegex(ValueError,'already'):research.add_symbol('AAPL')
            with self.assertRaises(ValueError):research.add_symbol('../file')
            market.st.session_state['shortlist']=['AAPL','MSFT','NVDA','SPY','TSLA','GOOGL','AMZN','META']
            with self.assertRaisesRegex(ValueError,'eight'):research.add_symbol('TCS.NS')

class WorkspaceTests(unittest.TestCase):
    def test_bookmarked_watchlist_restores_on_another_page(self):
        app=AppTest.from_file(str(ROOT/'pages/Analyzer.py'),default_timeout=40)
        app.query_params['watch']='AAPL,TSLA'
        app.run()
        self.assertEqual(app.session_state['shortlist'],['AAPL','TSLA'])
        self.assertEqual(list(app.exception),[])

    def test_linked_study_updates_previous_completed_stock(self):
        app=AppTest.from_file(str(ROOT/'pages/Analyzer.py'),default_timeout=40).run()
        self.assertEqual(app.session_state['study']['ticker'],'AAPL')
        app.query_params['ticker']='NVDA';app.run()
        self.assertEqual(app.session_state['study']['ticker'],'NVDA')
        self.assertEqual(app.text_input[0].value,'NVDA')
        self.assertEqual(list(app.exception),[])

    def test_scenario_controls_keep_scenario_view_and_watchlist_can_be_edited(self):
        app=AppTest.from_file(str(ROOT/'pages/Analyzer.py'),default_timeout=40).run()
        app.slider[0].set_value(40).run()
        self.assertEqual(app.session_state['research_tab'],'Scenarios')
        self.assertEqual(list(app.exception),[])
        board=AppTest.from_file(str(ROOT/'pages/Dashboard.py'),default_timeout=40).run()
        board.text_input[0].set_value('TSLA')
        board.button[1].click().run()
        self.assertIn('TSLA',board.session_state['shortlist'])
        self.assertEqual(list(board.exception),[])

if __name__=='__main__':unittest.main()
