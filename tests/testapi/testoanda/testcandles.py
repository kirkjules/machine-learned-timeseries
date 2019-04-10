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


if __name__ == "__main__":
    unittest.main()
