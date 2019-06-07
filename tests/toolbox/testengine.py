import unittest
import logging
import pandas as pd
# from pprint import pprint
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
        Test download returns values for all business days.
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
        print(nval)
        self.assertEqual(len(nval), 0)


if __name__ == "__main__":
    unittest.main()
