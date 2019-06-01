import os
import pandas
import unittest
import logging
from pprint import pprint
from htp.api import oanda, exceptions

logging.basicConfig(level=logging.INFO)


class TestCandles(unittest.TestCase):

    """
    def test_requests_exception(self):
        # Test request library extension raising.
        ticker = "EUR_USD"
        arguments = {"count": "6", "price": "M", "granularity": "S5"}

        with self.assertRaises(exceptions.ApiError):
            oanda.Candles(instrument=ticker,
                          queryParameters=arguments)
    """

    def test_response(self):
        """
        Test HTTP response type.
        """

        ticker = "EUR_USD"
        arguments = {"count": "6", "price": "M", "granularity": "S5"}
        cf = os.path.join(os.path.dirname(__file__), "../..", "config.yaml")
        data = oanda.Candles(configFile=cf, instrument=ticker,
                             queryParameters=arguments)
        pprint(data.json())
        self.assertEqual(data.r.status_code, 200)

    def test_oanda_response(self):
        """
        Test forced Oanda http responses.
        """
        arguments = {"count": "6", "price": "M", "granularity": "S5"}
        errors = {400: {"ticker": "XYZ_ABC",
                        "arguments": arguments},
                  401: {"ticker": "EUR_USD",
                        "arguments": arguments}}

        for i in errors.keys():
            with self.subTest(i=i):
                try:
                    oanda.Candles(instrument=errors[i]["ticker"],
                                  queryParameters=errors[i]["arguments"])
                except exceptions.OandaError as e:
                    print(e)
                    self.assertEqual(e.status_code, i)

    def test_out(self):
        """
        Test the function output defined by outFile argument.
        """

        ticker = "EUR_USD"
        arguments = {"count": "6", "price": "M", "granularity": "S5"}

        r = oanda.Candles(instrument=ticker, queryParameters=arguments)

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
                    r.df(outFile="tests/api/out/out.csv")
                    out_dir = os.listdir("tests/api/out/")
                    filename, file_ext = os.path.splitext(out_dir[0])
                    self.assertEqual(file_ext, ".csv")


if __name__ == "__main__":
    unittest.main()
