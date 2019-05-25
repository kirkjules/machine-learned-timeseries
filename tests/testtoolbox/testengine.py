import unittest
import logging
from pprint import pprint
from api import oanda
from toolbox import dates, engine

f = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=f)


class TestDownloadWorker(unittest.TestCase):

    def test_initialising(self):
        """
        Test parsing functionality for class initiation.
        """
        date_gen = dates.Select().by_month(period=5)
        func = oanda.Candles
        configFile = "config.ini"
        instrument = "AUD_JPY"
        queryParameters = {"granularity": "D", "smooth": True}
        live = False
        work = engine.Worker(date_gen=date_gen,
                             func=func,
                             configFile=configFile,
                             instrument=instrument,
                             queryParameters=queryParameters,
                             live=live)
        for i in ["date_gen", "kwargs", "func"]:
            with self.subTest(i=i):
                if i == "date_gen":
                    # pprint(work.arg_list)
                    self.assertEqual(len(work.arg_list), 5)
                elif i == "kwargs":
                    self.assertEqual(len(work.kwargs), 4)
                elif i == "func":
                    work.kwargs["queryParameters"]["from"] = \
                        "2019-05-12T15:00:00.000000000Z"
                    work.kwargs["queryParameters"]["to"] = \
                        "2019-05-15T09:00:00.000000000Z"
                    f = work.func(work.kwargs["configFile"],
                                  work.kwargs["instrument"],
                                  work.kwargs["queryParameters"],
                                  work.kwargs["live"])
                    self.assertEqual(f.status, 200)

    def test_run_single(self):
        """
        Test download functionality for sequential engine.
        """
        queue = dates.Select().by_month(period=5)
        func = oanda.Candles
        configFile = "config.ini"
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

    def test_run_single_error_handling(self):
        """
        Test download functionality for sequential engine.
        """
        queue = dates.Select().by_month(period=5)
        func = oanda.Candles
        configFile = "config.ini"
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
        self.assertEqual(len(d), 5)

    def test_run_concurrently_error_handling(self):
        """
        Test download functionality for concurrent engine.
        """
        queue = dates.Select().by_month(period=5)
        func = oanda.Candles
        configFile = "config.ini"
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
        pprint(d)
        self.assertEqual(len(d), 5)

    def test_run_parallel_error_handling(self):
        """
        Test download functionality for parallel engine.
        """
        queue = dates.Select().by_month(period=5)
        date_list = []
        for i in queue:
            date_list.append(i)
        func = oanda.Candles
        configFile = "config.ini"
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
        pprint(d)
        self.assertEqual(len(d), 5)


if __name__ == "__main__":
    unittest.main()
