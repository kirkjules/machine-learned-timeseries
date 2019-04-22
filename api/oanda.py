import logging
from . import Api
import requests
import exceptions
import pandas as pd

log = logging.getLogger(__name__)


class Instrument(Api):

    def candles(self, instrument, queryParameters, outType=None,
                outFile=None):
        """Request query parameters are: price, granularity, count,
        from, to, smooth, includeFirst, dailyAlignment, alignmentTimezone,
        weeklyAlignment.
        Refer to http://developer.oanda.com/rest-live-v20/instrument-ep/
        for parameter descriptions.

        Optional arguments outType and outDir can be specified if the return
        should not be a request object.
        """

        url = self.base + "instruments/{0}/candles?"

        r = requests.get(url.format(instrument),
                         headers=self.headers,
                         params=queryParameters)
        
        try:
            r.status_code == 200
        except excpetions.Oanda as e:
            raise(e)

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
                return df.to_csv(outFile)

        else:
            print("Error")


if __name__ == "__main__":

    ticker = "EUR_USD"
    arguments = {"count": "6", "price": "M", "granularity": "S5"}
    r = Instrument("api/config.ini", live=False)
    data = r.candles(ticker, arguments)
    print(data.json())
