# import configparser
from . import Api
import requests
import pandas as pd
import logging

log = logging.getLogger(__name__)


"""
class Api:

    def __init__(self, configFile):

        config = configparser.ConfigParser()
        with open(configFile, 'r') as f:
            config.read_file(f)
        self.sections = config.sections()
        self.key = config["api-fxpractice.oanda.com"]["authtoken"]
"""


class Instrument(Api):

    def candles(self, instrument, queryParameters, outType=None,
                outDir=None):
        """Request query parameters are: price, granularity, count,
        from, to, smooth, includeFirst, dailyAlignment, alignmentTimezone,
        weeklyAlignment.
        Refer to http://developer.oanda.com/rest-live-v20/instrument-ep/
        for parameter descriptions.

        Optional arguments outType and outDir can be specified if the return
        should not be a request object.
        """

        headers = {"Content-Type": "application/json",
                   "Authorization": "Bearer {0}".format(self.key)}

        url = "https://api-fxpractice.oanda.com/v3/instruments/{0}/candles?"

        r = requests.get(url.format(instrument),
                         headers=headers,
                         params=queryParameters)

        if outType is None:
            return r

        elif outType == "json":
            return r.json()

        elif outType == "pandas" or outType == "csv":

            dic = {}

            cols = {"o": "open", "h": "high", "l": "low", "c": "close"}

            for i in range(len(r.json()["candles"])):
                dic[r.json()["candles"][i]["time"]] =\
                        r.json()["candles"][i]["mid"]

            df = pd.DataFrame.from_dict(dic,
                                        orient="index").rename(columns=cols)

            if outType == "pandas":
                return df

            elif outType == "csv":
                return df.to_csv(outDir)

        else:
            print("Error")


if __name__ == "__main__":

    ticker = "EUR_USD"
    arguments = {"count": "6", "price": "M", "granularity": "S5"}
    r = Instrument("api/config.ini")
    data = r.candles(ticker, arguments)
    print(data.json())
