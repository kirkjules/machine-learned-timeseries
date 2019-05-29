import logging
import requests
import pandas as pd
from . import Api, exceptions

log = logging.getLogger(__name__)


class Candles(Api):

    def __init__(self, configFile="config.yaml", api="oanda",
                 access="practise", **kwargs):
        # configFile, instrument, queryParameters, live):
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
        super().__init__(configFile, api, access, **kwargs)  # configFile, live
        self.headers = {"Content-Type": "application/json",
                        "Authorization": "Bearer {0}"
                        .format(self.details["token"])}
        self.instrument = kwargs["instrument"]
        self.url = self.details["url"] + "instruments/{0}/candles?".format(
            self.instrument)
        self.queryParameters = kwargs["queryParameters"]

        try:
            self.r = requests.get(self.url,
                                  headers=self.headers,
                                  params=self.queryParameters)
        except requests.exceptions.RequestException as e:
            exc = exceptions.ApiError("There has been an error connecting"
                                      " with the api endpoint as raised by: "
                                      " {}".format(e))
            # log.info(exc)
            raise exc from None
        else:
            self.status = self.r.status_code

            if self.r.status_code != 200:
                raise exceptions.OandaError(
                  "The instrument.Candles endpoint has returned the following"
                  " error",
                  self.r.json(),
                  status_code=self.r.status_code)

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
