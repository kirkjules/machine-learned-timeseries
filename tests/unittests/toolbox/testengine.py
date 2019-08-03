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
        instrument = "AUD_JPY"
        queryParameters = {"granularity": "D", "smooth": True}
        work = engine.Worker(configFile="config.yaml",
                             date_gen=date_gen,
                             func=func,
                             instrument=instrument,
                             queryParameters=queryParameters)
        for i in ["date_gen", "kwargs", "func"]:
            with self.subTest(i=i):
                if i == "date_gen":
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
        work = engine.Worker(date_gen=queue,
                             func=func,
                             configFile=configFile,
                             instrument=instrument,
                             queryParameters=queryParameters)
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
        work = engine.Worker(date_gen=queue,
                             func=func,
                             configFile=configFile,
                             instrument=instrument,
                             queryParameters=queryParameters)
        d = work.run()
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
        work = engine.ConcurrentWorker(date_gen=queue,
                                       func=func,
                                       configFile=configFile,
                                       instrument=instrument,
                                       queryParameters=queryParameters)
        d = work.run()
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
        work = engine.ParallelWorker(date_gen=date_list,
                                     func=func,
                                     configFile=configFile,
                                     instrument=instrument,
                                     queryParameters=queryParameters)
        d = work.run()
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
                             ).by_month(no_days=[6])
        func = oanda.Candles.to_df
        configFile = "config.yaml"
        instrument = "AUD_JPY"
        queryParameters = {"granularity": "M15", "smooth": True}
        work = engine.ConcurrentWorker(date_gen=queue,
                                       func=func,
                                       configFile=configFile,
                                       instrument=instrument,
                                       queryParameters=queryParameters)
        d = work.run()
        d_concat = pd.concat(d)
        d_clean = d_concat[~d_concat.index.duplicated()]
        check = pd.read_csv("data/AUD_JPYD2005-2015.csv")
        check_indexset = check.set_index("Unnamed: 0")
        check_joined = check_indexset.join(d_clean, how="left", rsuffix="_d",
                                           lsuffix="_check")
        nval = check_joined[check_joined["open_d"].isnull()]
        print("Unmatched: {}".format(len(nval)))
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

    def test_index_check_quarter_month_HONE(self):
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

        Note: the Oanda API will not return the candle for the `to` timestamp.
        """
        print("\nRun Index Check on Quarter v Month by H1\n")
        func = oanda.Candles.to_df
        configFile = "config.yaml"
        instrument = "AUD_JPY"
        queryParameters = {"granularity": "H1", "smooth": True}
        queue_quarter = dates.Select(from_="2005-01-01 17:00:00",
                                     to="2015-12-30 17:00:00",
                                     local_tz="America/New_York"
                                     ).by_quarter(no_days=[6])
        work = engine.ConcurrentWorker(date_gen=queue_quarter,
                                       func=func,
                                       configFile=configFile,
                                       instrument=instrument,
                                       queryParameters=queryParameters)
        quarter = work.run()
        quarter_concat = pd.concat(quarter)
        quarter_clean = quarter_concat[~quarter_concat.index.duplicated()]
        queue_month = dates.Select(from_="2005-01-01 17:00:00",
                                   to="2015-12-30 17:00:00",
                                   local_tz="America/New_York"
                                   ).by_month(no_days=[6])
        work = engine.ConcurrentWorker(date_gen=queue_month,
                                       func=func,
                                       configFile=configFile,
                                       instrument=instrument,
                                       queryParameters=queryParameters)
        month = work.run()
        month_concat = pd.concat(month)
        month_clean = month_concat[~month_concat.index.duplicated()]
        quarter_month = quarter_clean.join(month_clean,
                                           how="left", rsuffix="_d",
                                           lsuffix="_check")
        nval = quarter_month[quarter_month["open_d"].isnull()]
        print("Record # By Quarter: {}".format(len(quarter_clean)))
        print("Record # By Month: {}".format(len(month_clean)))
        print("Unmatched: {}".format(len(nval)))
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

    def test_index_check_quarter_week_HONE(self):
        """
        Test AUD_JPY returned datetime values' consistency by cross checking
        between two data sets generated, by_quarter and by_week respectively
        across same time range (2005-2015) with same granularity (H1).
        """

        print("\nRun Index Check on Quarter v Week by H1\n")
        func = oanda.Candles.to_df
        configFile = "config.yaml"
        instrument = "AUD_JPY"
        queryParameters = {"granularity": "H1", "smooth": True}
        queue_quarter = dates.Select(from_="2005-01-01 17:00:00",
                                     to="2015-12-30 17:00:00",
                                     local_tz="America/New_York"
                                     ).by_quarter(no_days=[6])
        work = engine.ConcurrentWorker(date_gen=queue_quarter,
                                       func=func,
                                       configFile=configFile,
                                       instrument=instrument,
                                       queryParameters=queryParameters)
        quarter = work.run()
        quarter_concat = pd.concat(quarter)
        quarter_clean = quarter_concat[~quarter_concat.index.duplicated()]
        queue_week = dates.Select(from_="2005-01-01 17:00:00",
                                  to="2015-12-30 17:00:00",
                                  local_tz="America/New_York"
                                  ).by_week(no_days=[6])
        work = engine.ConcurrentWorker(date_gen=queue_week,
                                       func=func,
                                       configFile=configFile,
                                       instrument=instrument,
                                       queryParameters=queryParameters)
        week = work.run()
        week_concat = pd.concat(week)
        week_clean = week_concat[~week_concat.index.duplicated()]
        quarter_week = quarter_clean.join(week_clean,
                                          how="left", rsuffix="_d",
                                          lsuffix="_check")
        nval = quarter_week[quarter_week["open_d"].isnull()]
        print("Record # By Quarter: {}".format(len(quarter_clean)))
        print("Record # By Week: {}".format(len(week_clean)))
        print("Unmatched: {}".format(len(nval)))
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

    def test_index_check_quarter_day_HONE(self):
        """
        Test AUD_JPY returned datetime values' consistency by cross checking
        between two data sets generated, by_quarter and by_day respectively
        across same time range (2005-2005) with same granularity (H1).
        """

        print("\nRun Index Check on Quarter v Day by H1\n")
        func = oanda.Candles.to_df
        configFile = "config.yaml"
        instrument = "AUD_JPY"
        queryParameters = {"granularity": "H1", "smooth": True}
        queue_quarter = dates.Select(from_="2005-01-01 17:00:00",
                                     to="2005-12-30 17:00:00",
                                     local_tz="America/New_York"
                                     ).by_quarter(no_days=[6])
        work = engine.ConcurrentWorker(date_gen=queue_quarter,
                                       func=func,
                                       configFile=configFile,
                                       instrument=instrument,
                                       queryParameters=queryParameters)
        quarter = work.run()
        quarter_concat = pd.concat(quarter)
        quarter_clean = quarter_concat[~quarter_concat.index.duplicated()]
        queue_week = dates.Select(from_="2005-01-01 17:00:00",
                                  to="2005-12-30 17:00:00",
                                  local_tz="America/New_York"
                                  ).by_day(no_days=[6])
        work = engine.ConcurrentWorker(date_gen=queue_week,
                                       func=func,
                                       configFile=configFile,
                                       instrument=instrument,
                                       queryParameters=queryParameters)
        day = work.run()
        day_concat = pd.concat(day)
        day_clean = day_concat[~day_concat.index.duplicated()]
        quarter_week = quarter_clean.join(day_clean,
                                          how="left", rsuffix="_d",
                                          lsuffix="_check")
        nval = quarter_week[quarter_week["open_d"].isnull()]
        print("Record # By Quarter: {}".format(len(quarter_clean)))
        print("Record # By Day: {}".format(len(day_clean)))
        print("Unmatched: {}".format(len(nval)))
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

    def test_index_check_calendar_year_quarter_HFOUR(self):
        """
        Test AUD_JPY returned datetime values' consistency by cross checking
        between two data sets generated, by_year and by_quarter respectively
        across same time range (2005-2015) with same granularity (H4).
        """

        print("\nRun Index Check on Calendar v Quarter by H4\n")
        func = oanda.Candles.to_df
        configFile = "config.yaml"
        instrument = "AUD_JPY"
        queryParameters = {"granularity": "H4", "smooth": True}
        queue_year = dates.Select(from_="2005-01-01 17:00:00",
                                  to="2015-12-30 17:00:00",
                                  local_tz="America/New_York"
                                  ).by_calendar_year(no_days=[6])
        work = engine.ConcurrentWorker(date_gen=queue_year,
                                       func=func,
                                       configFile=configFile,
                                       instrument=instrument,
                                       queryParameters=queryParameters)
        year = work.run()
        year_concat = pd.concat(year)
        year_clean = year_concat[~year_concat.index.duplicated()]
        queue_quarter = dates.Select(from_="2005-01-01 17:00:00",
                                     to="2015-12-30 17:00:00",
                                     local_tz="America/New_York"
                                     ).by_quarter(no_days=[6])
        work = engine.ConcurrentWorker(date_gen=queue_quarter,
                                       func=func,
                                       configFile=configFile,
                                       instrument=instrument,
                                       queryParameters=queryParameters)
        quarter = work.run()
        quarter_concat = pd.concat(quarter)
        quarter_clean = quarter_concat[~quarter_concat.index.duplicated()]
        year_quarter = year_clean.join(quarter_clean,
                                       how="left", rsuffix="_d",
                                       lsuffix="_check")
        nval = year_quarter[year_quarter["open_d"].isnull()]
        print("Record # By Calendar Year: {}".format(len(year_clean)))
        print("Record # By Quarter: {}".format(len(quarter_clean)))
        print("Unmatched: {}".format(len(nval)))
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

    def test_index_check_calendar_year_month_HFOUR(self):
        """
        Test AUD_JPY returned datetime values' consistency by cross checking
        between two data sets generated, by_year and by_month respectively
        across same time range (2005-2015) with same granularity (H4).
        """

        print("\nRun Index Check on Calendar v Month by H4\n")
        func = oanda.Candles.to_df
        configFile = "config.yaml"
        instrument = "AUD_JPY"
        queryParameters = {"granularity": "H4", "smooth": True}
        queue_year = dates.Select(from_="2005-01-01 17:00:00",
                                  to="2015-12-30 17:00:00",
                                  local_tz="America/New_York"
                                  ).by_calendar_year(no_days=[6])
        work = engine.ConcurrentWorker(date_gen=queue_year,
                                       func=func,
                                       configFile=configFile,
                                       instrument=instrument,
                                       queryParameters=queryParameters)
        year = work.run()
        year_concat = pd.concat(year)
        year_clean = year_concat[~year_concat.index.duplicated()]
        queue_month = dates.Select(from_="2005-01-01 17:00:00",
                                   to="2015-12-30 17:00:00",
                                   local_tz="America/New_York"
                                   ).by_month(no_days=[6])
        work = engine.ConcurrentWorker(date_gen=queue_month,
                                       func=func,
                                       configFile=configFile,
                                       instrument=instrument,
                                       queryParameters=queryParameters)
        month = work.run()
        month_concat = pd.concat(month)
        month_clean = month_concat[~month_concat.index.duplicated()]
        year_month = year_clean.join(month_clean,
                                     how="left", rsuffix="_d",
                                     lsuffix="_check")
        nval = year_month[year_month["open_d"].isnull()]
        print("Record # By Calendar Year: {}".format(len(year_clean)))
        print("Record # By Month: {}".format(len(month_clean)))
        print("Unmatched: {}".format(len(nval)))
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

    def test_index_check_calendar_year_week_HFOUR(self):
        """
        Test AUD_JPY returned datetime values' consistency by cross checking
        between two data sets generated, by_year and by_week respectively
        across same time range (2005-2015) with same granularity (H4).
        """

        print("\nRun Index Check on Calendar v Week by H4\n")
        func = oanda.Candles.to_df
        configFile = "config.yaml"
        instrument = "AUD_JPY"
        queryParameters = {"granularity": "H4", "smooth": True}
        queue_year = dates.Select(from_="2005-01-01 17:00:00",
                                  to="2015-12-30 17:00:00",
                                  local_tz="America/New_York"
                                  ).by_calendar_year(no_days=[6])
        work = engine.ConcurrentWorker(date_gen=queue_year,
                                       func=func,
                                       configFile=configFile,
                                       instrument=instrument,
                                       queryParameters=queryParameters)
        year = work.run()
        year_concat = pd.concat(year)
        year_clean = year_concat[~year_concat.index.duplicated()]
        queue_week = dates.Select(from_="2005-01-01 17:00:00",
                                  to="2015-12-30 17:00:00",
                                  local_tz="America/New_York"
                                  ).by_week(no_days=[6])
        work = engine.ConcurrentWorker(date_gen=queue_week,
                                       func=func,
                                       configFile=configFile,
                                       instrument=instrument,
                                       queryParameters=queryParameters)
        week = work.run()
        week_concat = pd.concat(week)
        week_clean = week_concat[~week_concat.index.duplicated()]
        year_week = week_clean.join(week_clean,
                                    how="left", rsuffix="_d",
                                    lsuffix="_check")
        nval = year_week[year_week["open_d"].isnull()]
        print("Record # By Calendar Year: {}".format(len(year_clean)))
        print("Record # By Week: {}".format(len(week_clean)))
        print("Unmatched: {}".format(len(nval)))
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

    def test_index_check_calendar_year_financial_year_HFOUR(self):
        """
        Test AUD_JPY returned datetime values' consistency by cross checking
        between two data sets generated, by_year and by_financial_year
        respectively across same time range (2005-2015) with same granularity
        (H4).
        """

        print("\nRun Index Check on Calendar v Financial Year by H4\n")
        func = oanda.Candles.to_df
        configFile = "config.yaml"
        instrument = "AUD_JPY"
        queryParameters = {"granularity": "H4", "smooth": True}
        queue_year = dates.Select(from_="2005-01-01 17:00:00",
                                  to="2015-12-30 17:00:00",
                                  local_tz="America/New_York"
                                  ).by_calendar_year(no_days=[6])
        work = engine.ConcurrentWorker(date_gen=queue_year,
                                       func=func,
                                       configFile=configFile,
                                       instrument=instrument,
                                       queryParameters=queryParameters)
        year = work.run()
        year_concat = pd.concat(year)
        year_clean = year_concat[~year_concat.index.duplicated()]
        queue_financial = dates.Select(from_="2005-01-01 17:00:00",
                                       to="2015-12-30 17:00:00",
                                       local_tz="America/New_York"
                                       ).by_financial_year(no_days=[6])
        work = engine.ConcurrentWorker(date_gen=queue_financial,
                                       func=func,
                                       configFile=configFile,
                                       instrument=instrument,
                                       queryParameters=queryParameters)
        financial = work.run()
        financial_concat = pd.concat(financial)
        financial_clean = financial_concat[
            ~financial_concat.index.duplicated()]
        year_financial = year_clean.join(financial_clean,
                                         how="left", rsuffix="_d",
                                         lsuffix="_check")
        nval = year_financial[year_financial["open_d"].isnull()]
        print("Record # By Calendar Year: {}".format(len(year_clean)))
        print("Record # By Financial Year: {}".format(len(financial_clean)))
        print("Unmatched: {}".format(len(nval)))
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


if __name__ == "__main__":
    unittest.main()
