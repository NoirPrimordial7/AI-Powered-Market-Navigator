import unittest
import numpy as np
from market import get_data,FEATURES
from training import prepare

class TrainingProtocolTests(unittest.TestCase):
    def test_future_extrema_cannot_change_training_scaler_or_examples(self):
        data=get_data('AAPL')
        clean,scaler,parts,targets,bounds=prepare(data)
        changed=data.copy();changed.loc[clean.index[bounds[0]:],FEATURES]=changed.loc[clean.index[bounds[0]:],FEATURES]*100
        _,other,altered,_,_=prepare(changed)
        np.testing.assert_array_equal(scaler.data_max_,other.data_max_)
        np.testing.assert_array_equal(parts[0][0],altered[0][0])
        np.testing.assert_array_equal(parts[0][1],altered[0][1])
        self.assertEqual(parts[0][0].shape[1:],(30,11))
        self.assertEqual(sum(len(x) for x,y in parts),len(clean)-30)
        self.assertTrue(np.any(altered[2][0]>1))

    def test_next_session_target_follows_input_window(self):
        clean,scaler,parts,targets,bounds=prepare(get_data('AAPL'))
        scaled=scaler.transform(clean).astype('float32')
        np.testing.assert_array_equal(parts[0][0][0],scaled[:30])
        self.assertEqual(parts[0][1][0],scaled[30,FEATURES.index('Close')])
