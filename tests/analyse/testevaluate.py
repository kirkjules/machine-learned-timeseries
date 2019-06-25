import unittest
import pandas as pd
from htp.api import oanda
from htp.analyse import indicator, evaluate


class TestIndicator(unittest.TestCase):

    def test_buy_signal_cross(self):

        ticker = "AUD_JPY"
        arguments = {"from": "2018-02-05T22:00:00.000000000Z",
                     "granularity": "D",
                     "smooth": True,
                     "count": 50}
        data = oanda.Candles.to_df(instrument=ticker, queryParameters=arguments)
        data_index_dt = data.set_index(
            pd.to_datetime(data.index,
                           format="%Y-%m-%dT%H:%M:%S.%f000Z"), drop=True)
        data_sorted = data_index_dt.sort_index()
        sma_5 = indicator.smooth_moving_average(
            data_sorted, column="close", period=5)
        sma_5_10 = indicator.smooth_moving_average(
            data_sorted, df2=sma_5, column="close", concat=True, period=10)
        entry_exit = evaluate.buy_signal_cross(sma_5_10, "close_sma_5", "close_sma_10")
        self.assertEqual(str(type(entry_exit)),
                         "<class 'pandas.core.frame.DataFrame'>")
