import os
import pandas
import unittest
import logging
from api import oanda

logging.basicConfig(level=logging.INFO)


class TestCandles(unittest.TestCase):

    def test_response(self):
        """
        Test HTTP response type.
        """

        ticker = "EUR_USD"
        arguments = {"count": "6", "price": "M", "granularity": "S5"}
        cf = "config.ini"
        live = False

        data = oanda.Candles(cf, ticker, arguments, live)
        self.assertEqual(data.r.status_code, 200)

    def test_oanda_response(self):
        """
        Test Oanda error message logging.
        """

        ticker = "EUR_USD"
        arguments = {"count": "6", "price": "M", "granularity": "S5"}
        cf = "config.ini"
        live = True

        data = oanda.Candles(cf, ticker, arguments, live)
        self.assertEqual(data.r.status_code, 400)

    def test_out(self):
        """
        Test the function output defined by outFile argument.
        """

        cf = "config.ini"
        live = False

        ticker = "EUR_USD"
        arguments = {"count": "6", "price": "M", "granularity": "S5"}

        r = oanda.Candles(cf, ticker, arguments, live)

        out = {"json": dict,
               "pandas": pandas.core.frame.DataFrame,
               "csv": ".csv"}

        for i in out.keys():
            with self.subTest(i=i):
                if i == "json":
                    data = r.json()
                    self.assertEqual(type(data), out[i])

                elif i == "pandas":
                    data = r.df()
                    self.assertEqual(type(data), out[i])

                elif i == "csv":
                    r.df(outFile="tests/testapi/testoanda/out/out.csv")
                    out_dir = os.listdir("tests/testapi/testoanda/out/")
                    filename, file_ext = os.path.splitext(out_dir[0])
                    self.assertEqual(file_ext, ".csv")


if __name__ == "__main__":
    unittest.main()
