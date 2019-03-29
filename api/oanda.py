import configparser
import requests


class Api:

    def __init__(self, configFile):

        config = configparser.ConfigParser()
        with open(configFile, 'r') as f:
            config.read_file(f)
        self.sections = config.sections()
        self.key = config["api-fxpractice.oanda.com"]["authtoken"]


class Instrument(Api):

    def candles(self, instrument, queryParameters):
        """Request query parameters are: price, granularity, count,
        from, to, smooth, includeFirst, dailyAlignment, alignmentTimezone,
        weeklyAlignment.
        Refer to http://developer.oanda.com/rest-live-v20/instrument-ep/
        for parameter descriptions.
        """

        headers = {"Content-Type": "application/json",
                   "Authorization": "Bearer {0}".format(self.key)}
        url = "https://api-fxpractice.oanda.com/v3/instruments/{0}/candles?"

        return requests.get(url.format(instrument),
                            headers=headers,
                            params=queryParameters)


if __name__ == "__main__":

    ticker = "EUR_USD"
    arguments = {"count": "6", "price": "M", "granularity": "S5"}
    r = Instrument("api/config.ini")
    data = r.candles(ticker, arguments)
    print(data.json())