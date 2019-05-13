import logging
import requests
import pandas as pd
from . import Api, exceptions

log = logging.getLogger(__name__)


class Candles(Api):

    def __init__(self, configFile, instrument, queryParameters, live):
        """Request query parameters are: price, granularity, count,
        from, to, smooth, includeFirst, dailyAlignment, alignmentTimezone,
        weeklyAlignment.
        Refer to http://developer.oanda.com/rest-live-v20/instrument-ep/
        for parameter descriptions.
        Api behaviour will depend on Oanda releases. Notable mentions are:
            From and to parameters outside available ticker will return
            closest datetime results.
            Except where the to paramater is in the future.
            Where an inappropriate granularity is used which exceeds the
            maximum candle count value an error will be reported by the api
            with a HTTP 400 status and logged by the Candles class.
        """
        super().__init__(configFile, live)
        self.instrument = instrument
        self.queryParameters = queryParameters
        self.url = self.base + "instruments/{0}/candles?".format(
            self.instrument)
        self.r = requests.get(self.url,
                              headers=self.headers,
                              params=self.queryParameters)
        self.status = self.r.status_code

        if self.r.status_code != 200:
            log.info(str(exceptions.Oanda(obj=self.r)))

    def json(self):
        return self.r.json()

    def df(self, outFile=None):

        dic = {}

        cols = {"o": "open", "h": "high", "l": "low", "c": "close"}

        for i in range(len(self.r.json()["candles"])):
            dic[self.r.json()["candles"][i]["time"]] =\
                    self.r.json()["candles"][i]["mid"]

        data = pd.DataFrame.from_dict(dic, orient="index").rename(columns=cols)

        if outFile is None:
            return data
        else:
            return data.to_csv(outFile)


if __name__ == "__main__":

    ticker = "EUR_USD"
    arguments = {"count": "6", "price": "M", "granularity": "S5"}
    r = Candles("api/config.ini", ticker, arguments, live=False)
    data = r.json()
    print(data.json())
