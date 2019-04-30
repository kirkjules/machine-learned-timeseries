import logging
import unittest
import time
import pytz
from datetime import datetime, timedelta
from toolbox import dates

logging.basicConfig(level=logging.INFO)


class TestConversion(unittest.TestCase):

    def test_input(self):
        """
        Test valid date string input.
        """
        local_tz = time.strftime("%z", time.localtime())  # e.g. +0700
        timestamps = ["2014-05-13 16:04:32", "2014/05/13 12:09:01",
                      "18/08/1993 09:32:10", "2003-13-12 10:00:00",
                      "09/30/2009 02:19:43", "2005-01-04 28:59:02"]

        for i in range(len(timestamps)):
            with self.subTest(exp=timestamps[i]):
                if i == 0:
                    t = dates.Conversion(timestamps[i])
                    self.assertEqual(datetime.strftime(t.tz_date,
                                                       "%Y-%m-%d %H:%M:%S%z"),
                                     timestamps[i] + local_tz)
                else:
                    with self.assertRaises(ValueError):
                        dates.Conversion(timestamps[i])

    def test_local_tz(self):
        """
        Test valid local tz input and resulting datetime awareness.
        """
        tz = {"America/New_York": "-0400", "Asia/Tokyo": "+0900",
              "Europe/Paris": "+0200", "XYZ/ABC": "+0000", None: "+0700"}
        for i in tz.keys():
            with self.subTest(exp=i):
                t = dates.Conversion("2014-04-13 16:04:32", local_tz=i)
                # print(t.tz_date, i)
                self.assertEqual(datetime.strftime(t.tz_date, "%z"), tz[i])

    def test_utc_date(self):
        """
        Test UTC conversion of localised datetime objects.
        """
        tz = {"America/New_York": "-4", "Asia/Tokyo": "+9",
              "Europe/Paris": "+2", "XYZ/ABC": "+0", None: "+7"}
        for i in tz.keys():
            with self.subTest(exp=i):
                t = dates.Conversion("2014-04-13 16:04:32", local_tz=i)
                # print(t.tz_date, i)
                c_t = (t.tz_date.replace(tzinfo=pytz.utc)
                       + timedelta(hours=int(tz[i]) * -1))
                self.assertEqual(datetime.strftime(t.utc_date,
                                                   "%Y-%m-%d %H:%M:%S%z"),
                                 datetime.strftime(c_t, "%Y-%m-%d %H:%M:%S%z"))


class TestSelect(unittest.TestCase):

    def test_input(self):
        """
        Test datestring and local_tz input and conversion.
        """
        from_ = "2019-04-16 18:32:21"
        local_tz = "Australia/Sydney"
        self.assertEqual(datetime.strftime(dates.Select(from_=from_,
                                                        local_tz=local_tz
                                                        ).from_date,
                                           "%Y-%m-%d %H:%M:%S%z"),
                         "2019-04-16 08:32:21+0000")

    def test_time_val(self):
        """
        Test time_val for function integrity.
        """
        date = datetime(2018, 12, 31)
        self.assertEqual(dates.Select().time_val(date=date,
                                                 select=-1,
                                                 hour=17,
                                                 by_year=True),
                         datetime(2018, 12, 30, 17))


if __name__ == "__main__":
    unittest.main()
