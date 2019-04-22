import os
import pandas
import requests
import unittest
from api import oanda


class TestCandles(unittest.TestCase):

    def test_response(self):
        """
        Test HTTP response type.
        """

        ticker = "EUR_USD"
        arguments = {"count": "6", "price": "M", "granularity": "S5"}
        cf = "config.ini"

        r = oanda.Instrument(cf)
        data = r.candles(ticker, arguments)
        self.assertEqual(data.status_code, 200)

    def test_output(self):
        """
        Test the function output defined by outType argument.
        """
        cf = "config.ini"
        r = oanda.Instrument(cf)

        ticker = "EUR_USD"
        arguments = {"count": "6", "price": "M", "granularity": "S5"}
        outType_ = {None: requests.models.Response,
                    "json": dict,
                    "pandas": pandas.core.frame.DataFrame,
                    "csv": ".csv"}
        for i in outType_.keys():
            data = r.candles(ticker, arguments, outType=i,
                             outFile="tests/testapi/testoanda/out/out.csv")
            if i == "csv":
                out_dir = os.listdir("tests/testapi/testoanda/out/")
                filename, file_ext = os.path.splitext(out_dir[0])
                self.assertEqual(file_ext, ".csv")
            else:
                self.assertEqual(type(data), outType_[i])


if __name__ == "__main__":
    unittest.main()
