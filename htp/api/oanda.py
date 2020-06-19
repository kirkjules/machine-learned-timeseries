"""
The oanda module contains functions that interact with the Oanda V20 API
endpoints, docummented at http://developer.oanda.com/rest-live-v20/introduction
"""
import sys
import requests
import pandas as pd
from loguru import logger
from pprint import pprint
from htp.api import Api, exceptions

logger.disable(__name__)


class Candles(Api):
    """
    A request operation that queries the Oanda instrument.Candles endpoint for
    a given ticker's timeseries data.

    The class inherits from Api, reading in relevant environment variables
    which are required to complete a GET HTTP request to the endpoint. A
    response object is initialised and, if the request is successful will
    contain the target timeseries data. Data manipulation is applied, as
    defined by class methods, to this object to yield differently structured
    data sets.

    Parameters
    ----------
    kwargs : str
        Arguments that specify endpoint parameter values.

    Attributes
    ---------
    instrument :  str
        A class attribute defined by a kwarg key, value pair with the key set
        to `instrument` and the value a string denoting the ticker available
        to being queried via the target endpoint.
    url : str
        The URL query string the defines the target endpoint.
    queryParameters : dict
        A class attribute defined by a kwarg, key, value pair with the key set
        to `queryParameters` and the value a dictionary with keys matching the
        available endpoint parameters and corresponding permitted value. See
        Notes.
    r : requests.models.Response
        The response object that contains the intended ticker timeseries data,
        as well as general HTTP response information such as the HTTP status
        code.
    status : int
        A class attribute that exposes the HTTP status code in a separate
        variable.

    Raises
    ------
    requests.exceptions.RequestException
        If the GET request has failed. This is a general exception defined in
        the requests library and will catch any error being raised by that
        library and any library that it uses. An example case is where
        it was not possible to connect to the URL's server due to a lack of
        network connection.

    exceptions.OandaException
        If the response status code is not 200. Here, the endpoint has provided
        a reason in the in the response body and this exposed by the exception.
        An example case is where the authorization token is incorrect.

    See Also
    --------
    htp.api : Api

    Notes
    -----
    The instrument.Candles endpoing posesses the following query parameters:
    price, granularity, count, from, to, smooth, includeFirst, dailyAlignment,
    alignmentTimezone, weeklyAlignment.
    Refer to http://developer.oanda.com/rest-live-v20/instrument-ep/
    for parameter descriptions.
    Api behaviour will depend on Oanda releases. Notable mentions are:

    * Parameters `from` and `to` set outside the daterange for what ticker
      timeseries data is available will be handled by the endpoint by querying
      the closest possible datetime values. The exception is where the `to`
      paramater is in the future.
    * Where an inappropriate granularity is used which exceeds the
      maximum candle count value an error will be reported by the api
      with a HTTP 400 status and logged by the Candles class.
    """

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.headers = {"Content-Type": "application/json",
                        "Authorization": f"Bearer {self.details['token']}"}
        self.instrument = kwargs["instrument"]
        self.url = f'https://api-fxpractice.oanda.com/v3/instruments/\
{self.instrument}/candles?'
        self.queryParameters = kwargs["queryParameters"]

        try:
            self.r = requests.get(self.url,
                                  headers=self.headers,
                                  params=self.queryParameters)
        except requests.exceptions.RequestException as e:
            raise exceptions.ApiError(
                "There has been an error connecting with the api endpoint as "
                "raised by: {}".format(e)) from None
        else:
            if self.r.status_code != requests.codes.ok:
                raise exceptions.OandaError(
                  "The instrument.Candles endpoint has returned the following"
                  " error", self.r.json(), self.r.status_code)
            else:
                pass

    @staticmethod
    def to_df(r, params):
        """Static function to process ticker data received from Oanda's
        instrument.Candles endpoint into a pandas DataFrame.

        Parameters
        ----------
        r : dict
            The dictionary returned by the instrumet.Candles endpoint.
        params : dict
            The parameters dictionary that was sent as an argument to the
        endpoint.

        Returns
        -------
        pandas.core.DataFrame
             Pandas DataFrame with a datetime index and open, high, low and
        close ticker value columns.
        """
        dic = {}
        price = {"M": "mid", "A": "ask", "B": "bid"}
        cols = {"o": "open", "h": "high", "l": "low", "c": "close"}
        for i in range(len(r["candles"])):
            dic[r["candles"][i]["time"]] = r["candles"][i][price[params]]
        data = pd.DataFrame.from_dict(
            dic, orient="index").rename(columns=cols)
        data.set_index(
            pd.to_datetime(data.index, format="%Y-%m-%dT%H:%M:%S.%f000Z"),
            drop=True, inplace=True)
        data.sort_index(inplace=True)
        return data


if __name__ == "__main__":
    """
    python htp/api/oanda.py "AUD_JPY" "2018-06-25T16:00:00.000000000Z" 5 "M15"
    """
    logger.enable("__main__")
    logger.add(
        sys.stdout, format="{time} - {level} - {message}", filter="__main__")
    ticker = sys.argv[1]
    queryParameters = {
        "from": sys.argv[2], "count": sys.argv[3], "granularity": sys.argv[4]}
    data = Candles(instrument=ticker, queryParameters=queryParameters).r.json()
    dic = {}
    if 'candles' in data:
        for candle in data['candles']:
            dic[candle['time'].replace('.000000000Z', '').replace('T', ' ')] =\
                    f"{candle['mid']['o']}, {candle['mid']['h']}"\
                    f", {candle['mid']['l']}, {candle['mid']['c']}"
    else:
        dic = data
    pprint(dic)
