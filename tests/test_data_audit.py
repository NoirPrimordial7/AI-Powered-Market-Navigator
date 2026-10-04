"""Check data-quality detection with an intentionally corrupted observation."""
import unittest
import pandas as pd
from audit_data import check_frame

class DataAuditTests(unittest.TestCase):
    def test_detects_corruption_and_future_date(self):
        frame=pd.DataFrame({'Open':[10,11],'High':[12,9],'Low':[8,10],'Close':[11,12],'Volume':[100,-1]},index=pd.to_datetime(['2026-10-01','2026-10-06']))
        result=check_frame(frame,pd.Timestamp('2026-10-05').date())
        self.assertFalse(result['structural_checks_pass'])
        self.assertEqual(result['errors']['future_dates'],1)
        self.assertEqual(result['errors']['negative_volume'],1)
        self.assertEqual(result['errors']['invalid_high_low_rows'],1)

    def test_valid_ohlcv_passes(self):
        frame=pd.DataFrame({'Open':[10,11],'High':[12,13],'Low':[8,10],'Close':[11,12],'Volume':[100,150]},index=pd.to_datetime(['2026-10-01','2026-10-02']))
        self.assertTrue(check_frame(frame,pd.Timestamp('2026-10-05').date())['structural_checks_pass'])
