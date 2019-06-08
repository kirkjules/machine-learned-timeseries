import unittest
import logging
import pandas as pd
from pprint import pprint
from htp.api import oanda
from htp.toolbox import dates, engine

f = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=f)


class TestDownloadWorker(unittest.TestCase):

    def test_initialising(self):
        """
        Test parsing functionality for class initiation.
        """
        date_gen = dates.Select().by_month(period=5)
        func = oanda.Candles
        # configFile = "config.ini"
        instrument = "AUD_JPY"
        queryParameters = {"granularity": "D", "smooth": True}
        # live = False
        work = engine.Worker(configFile="config.yaml",
                             date_gen=date_gen,
                             func=func,
                             instrument=instrument,
                             queryParameters=queryParameters)
        for i in ["date_gen", "kwargs", "func"]:
            with self.subTest(i=i):
                if i == "date_gen":
                    # pprint(work.arg_list)
                    self.assertEqual(len(work.arg_list), 5)
                elif i == "kwargs":
                    self.assertEqual(len(work.kwargs), 3)
                elif i == "func":
                    work.kwargs["queryParameters"]["from"] = \
                        "2019-05-12T15:00:00.000000000Z"
                    work.kwargs["queryParameters"]["to"] = \
                        "2019-05-15T09:00:00.000000000Z"
                    f = work.func(**{"instrument":
                                     work.kwargs["instrument"],
                                     "queryParameters":
                                     work.kwargs["queryParameters"]})
                    self.assertEqual(f.status, 200)

    def test_run_single(self):
        """
        Test download functionality for sequential engine.
        """
        print("\nRun Sequentially\n")
        queue = dates.Select().by_month(period=5)
        func = oanda.Candles.to_df
        configFile = "config.yaml"
        instrument = "AUD_JPY"
        queryParameters = {"granularity": "D", "smooth": True}
        live = False
        work = engine.Worker(date_gen=queue,
                             func=func,
                             configFile=configFile,
                             instrument=instrument,
                             queryParameters=queryParameters,
                             live=live)
        d = work.run()
        self.assertEqual(len(d), 5)

    def test_run_single_set_from(self):
        """
        Test download functionality for sequential engine.
        """
        print("\nRun Sequentially (w. set from date)\n")
        queue = dates.Select(from_="2018-12-19"
                             " 21:00:00",
                             to="2019-06-07"
                             " 05:10:30").by_month(no_days=[5, 6])
        func = oanda.Candles.to_df
        configFile = "config.yaml"
        instrument = "AUD_JPY"
        queryParameters = {"granularity": "D", "smooth": True}
        live = False
        work = engine.Worker(date_gen=queue,
                             func=func,
                             configFile=configFile,
                             instrument=instrument,
                             queryParameters=queryParameters,
                             live=live)
        d = work.run()
        # pprint(d)
        self.assertEqual(len(d), 7)

    def test_run_concurrently(self):
        """
        Test download functionality for concurrent engine.
        """
        print("\nRun Concurrently\n")
        queue = dates.Select().by_month(period=5)
        func = oanda.Candles.to_df
        configFile = "config.yaml"
        instrument = "AUD_JPY"
        queryParameters = {"granularity": "D", "smooth": True}
        live = False
        work = engine.ConcurrentWorker(date_gen=queue,
                                       func=func,
                                       configFile=configFile,
                                       instrument=instrument,
                                       queryParameters=queryParameters,
                                       live=live)
        d = work.run()
        # pprint(d)
        self.assertEqual(len(d), 5)

    def test_run_parallel(self):
        """
        Test download functionality for parallel engine.
        """
        print("\nRun in Parallel\n")
        queue = dates.Select().by_month(period=5)
        date_list = []
        for i in queue:
            date_list.append(i)
        func = oanda.Candles.to_df
        configFile = "config.yaml"
        instrument = "AUD_JPY"
        queryParameters = {"granularity": "D", "smooth": True}
        live = False
        work = engine.ParallelWorker(date_gen=date_list,
                                     func=func,
                                     configFile=configFile,
                                     instrument=instrument,
                                     queryParameters=queryParameters,
                                     live=live)
        d = work.run()
        # pprint(d)
        self.assertEqual(len(d), 5)

    def test_index_check(self):
        """
        Test returned datetime values' consistency by cross checking between
        two data sets:
            1. The key dataset is a bulk 2005-2015 download at the daily
            granularity.
            2. The tested dataset is generated for the same date range but with
            a smaller increment dates generator as well as a smaller
            granularity.

        Note, the results reflect that larger granularities will average/group
        ohlc values for a time range that may lack continuous data points.
        E.g. The daily 2013-02-01 22:00:00 is generated from data points at
        2013-02-01 22:15:00.
        A check can be performed to confirm this by querying the specifc
        datetime value signalled by the key dataset at the testing granularity.
        If the return is approximated to another datetime than this confirms
        the hypothesis.
        E.g.
        >>> ticker = "AUD_JPY"
        >>> arguments = {"count": 1, "from": "2013-02-02T22:00:00.000000000Z",
                         "granularity": "M15"}
        >>> data = oanda.Candles(instrument=ticker, queryParameters=arguments)
        >>> data.r.json()
        {'instrument': 'AUD_JPY',
         'granularity': 'M15',
         'candles': [{'complete': True,
         'volume': 323,
         'time': '2013-02-03T20:00:00.000000000Z',
         'mid': {'o': '96.550', 'h': '96.709', 'l': '96.540', 'c': '96.696'}}]}
        """
        print("\nRun Index Check\n")
        queue = dates.Select(from_="2005-01-01 17:00:00",
                             to="2015-12-30 17:00:00",
                             local_tz="America/New_York"
                             ).by_month(no_days=[5, 6])
        func = oanda.Candles.to_df
        configFile = "config.yaml"
        instrument = "AUD_JPY"
        queryParameters = {"granularity": "M15", "smooth": True}
        live = False
        work = engine.ConcurrentWorker(date_gen=queue,
                                       func=func,
                                       configFile=configFile,
                                       instrument=instrument,
                                       queryParameters=queryParameters,
                                       live=live)
        d = work.run()
        d_ = pd.concat(d)  # pprint(d)
        check = pd.read_csv("data/AUD_JPYD2005-2015.csv")
        check_indexset = check.set_index("Unnamed: 0")
        # d_joined = d_.join(check_indexset, how="inner", lsuffix="_d",
        #                    rsuffix="_check")
        check_joined = check_indexset.join(d_, how="left", rsuffix="_d",
                                           lsuffix="_check")
        nval = check_joined[check_joined["open_d"].isnull()]
        print(len(nval))
        for i in nval.index:
            with self.subTest(i=i):
                candle = \
                        oanda.Candles.to_json(instrument=instrument,
                                              queryParameters={"count": 1,
                                                               "from": i,
                                                               "granularity":
                                                               queryParameters
                                                               ["granularity"]
                                                               })
                pprint({i: candle})
                self.assertNotEqual(candle["candles"][0]["time"], i)
        # print(nval)
        # self.assertEqual(len(nval), 0)

    def test_index_check_same_granularity(self):
        """
        Test returned datetime values' consistency by cross checking between
        two data sets:
            1. The key dataset is queried from a larger increment dates
            generator at a given granularity.
            2. The tested dataset is generated for the same date range but with
            a smaller increment dates generator at the same granularity.

        There should be perfect matching if the smaller increment dates
        generator doesn't skip any datetime values contained in the key
        dataset. This is because both datasets have the same granularity, so
        datetime values should automatically increment equivalently.

        Learnt that the Oanda API will not return the candle for the `to`
        timestamp.
        """
        print("\nRun Index Check\n")
        func = oanda.Candles.to_df
        configFile = "config.yaml"
        instrument = "AUD_JPY"
        queryParameters = {"granularity": "H1", "smooth": True}
        queue_large = dates.Select(from_="2005-01-01 17:00:00",
                                   to="2015-12-30 17:00:00",
                                   local_tz="America/New_York"
                                   ).by_quarter(no_days=[6],
                                                to_minute=0)
        work = engine.ConcurrentWorker(date_gen=queue_large,
                                       func=func,
                                       configFile=configFile,
                                       instrument=instrument,
                                       queryParameters=queryParameters)
        check = work.run()
        check_indexset = pd.concat(check)  # pprint(d)
        queue_small = dates.Select(from_="2005-01-01 17:00:00",
                                   to="2015-12-30 17:00:00",
                                   local_tz="America/New_York"
                                   ).by_month(no_days=[6],
                                              to_minute=0)
        work = engine.ConcurrentWorker(date_gen=queue_small,
                                       func=func,
                                       configFile=configFile,
                                       instrument=instrument,
                                       queryParameters=queryParameters)
        d = work.run()
        d_ = pd.concat(d)  # pprint(d)
        # check = pd.read_csv("data/AUD_JPYD2005-2015.csv")
        # check_indexset = check.set_index("Unnamed: 0")
        # d_joined = d_.join(check_indexset, how="inner", lsuffix="_d",
        #                    rsuffix="_check")
        check_joined = check_indexset.join(d_, how="left", rsuffix="_d",
                                           lsuffix="_check")
        nval = check_joined[check_joined["open_d"].isnull()]
        print(len(nval))
        if len(nval) > 0:
            for i in nval.index:
                with self.subTest(i=i):
                    candle = \
                            oanda.Candles.to_json(
                                instrument=instrument,
                                queryParameters={"count": 1,
                                                 "from": i,
                                                 "granularity":
                                                 queryParameters
                                                 ["granularity"]})
                    pprint({i: candle})
                    self.assertNotEqual(candle["candles"][0]["time"], i)
        else:
            self.assertEqual(len(nval), 0)
        # print(nval)
        # self.assertEqual(len(nval), 0)


if __name__ == "__main__":
    unittest.main()
