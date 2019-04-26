import logging
import unittest
import time
from datetime import datetime
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
                t = dates.Conversion(timestamps[i])
                if i == 0:
                    self.assertEqual(datetime.strftime(t.local,
                                                       "%Y-%m-%d %H:%M:%S%z"),
                                     timestamps[i] + local_tz)
                else:
                    self.assertEqual(t.local, None)


if __name__ == "__main__":
    unittest.main()
