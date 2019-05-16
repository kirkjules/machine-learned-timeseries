import unittest
import logging
from api import oanda
from toolbox import dates, engine

logging.basicConfig(level=logging.INFO)


class TestDownloadWorker(unittest.TestCase):

    def test_initialising(self):
        """
        Test parsing functionality for class initiation.
        """
        queue = dates.Select().by_month(period=10)
        func = oanda.Candles
        configFile = "config.ini"
        instrument = "AUD_JPY"
        queryParameters = {"granularity": "M15", "smooth": True}
        live = False
        work = engine.DownloadWorker(queue=queue,
                                     func=func,
                                     configFile=configFile,
                                     instrument=instrument,
                                     queryParameters=queryParameters,
                                     live=live)
        for i in ["queue", "kwargs", "func"]:
            with self.subTest(i=i):
                if i == "queue":
                    d = []
                    for j in work.queue:
                        d.append(j)
                    #    print(j)
                    self.assertEqual(len(d), 10)
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
        queue = dates.Select().by_month(period=10)
        func = oanda.Candles
        configFile = "config.ini"
        instrument = "AUD_JPY"
        queryParameters = {"granularity": "M15", "smooth": True}
        live = False
        work = engine.DownloadWorker(queue=queue,
                                     func=func,
                                     configFile=configFile,
                                     instrument=instrument,
                                     queryParameters=queryParameters,
                                     live=live)
        d = {}
        work.run_single(d)
        self.assertEqual(len(d), 10)


if __name__ == "__main__":
    unittest.main()
