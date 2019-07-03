"""
The oanda module contains functions that interact with the Oanda V20 API
endpoints, docummented at http://developer.oanda.com/rest-live-v20/introduction
"""
import sys
import requests
import pandas as pd
from loguru import logger
from htp.api import Api, exceptions

logger.disable(__name__)


class Candles(Api):
    """
    A request operation that queries the Oanda instrument.Candles endpoint for
    a given ticker's timeseries data.

    The class inherits from Api, reading in API variables from a `.yaml`
    configuration file which are required to complete a GET HTTP request to the
    endpoint. A response object is initialised and, if the request is
    successful will contain the target timeseries data. Data manipulation is
    applied, as defined by class methods, to this object to yield differently
    structured data sets.

    Parameters
    ----------
    kwargs : str
        Any extra keyword arguments that is required for class functionality.

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

    * Parameters `from` and `to` set outside the datarange for what ticker
      timeseries data is available will be handled by the endpoint by querying
      the closest possible datetime values. The exception is where the `to`
      paramater is in the future.
    * Where an inappropriate granularity is used which exceeds the
      maximum candle count value an error will be reported by the api
      with a HTTP 400 status and logged by the Candles class.

    Examples
    --------
    >>> import os
    >>> from pprint import pprint
    >>> from htp.api.oanda import Candles
    >>> ticker = "EUR_USD"
    >>> arguments = {"from": "2019-06-27T17:00:00.000000000Z", "count": "3"}
    >>> cf = os.path.join(os.path.dirname(__file__), "../..", "config.yaml")
    >>> data = Candles(
    ...     configFile=cf, instrument=ticker, queryParameters=arguments)
    >>> pprint(data.r.json())
    {'candles': [{'complete': True,
                  'mid': {'c': '1.13664',
                          'h': '1.13664',
                          'l': '1.13662',
                          'o': '1.13662'},
                  'time': '2019-06-27T17:00:00.000000000Z',
                  'volume': 2},
                 {'complete': True,
                  'mid': {'c': '1.13662',
                          'h': '1.13662',
                          'l': '1.13662',
                          'o': '1.13662'},
                  'time': '2019-06-27T17:00:05.000000000Z',
                  'volume': 1},
                 {'complete': True,
                  'mid': {'c': '1.13666',
                          'h': '1.13666',
                          'l': '1.13664',
                          'o': '1.13664'},
                  'time': '2019-06-27T17:00:10.000000000Z',
                  'volume': 2}],
     'granularity': 'S5',
     'instrument': 'EUR_USD'}
    """

    def __init__(self, configFile="config.yaml", api="oanda",
                 access="practise", **kwargs):
        super().__init__(configFile, api, access)  # , **kwargs)
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
            raise exceptions.ApiError(
                "There has been an error connecting with the api endpoint as "
                "raised by: {}".format(e)) from None
        else:
            status = self.r.status_code

            if status != 200:
                raise exceptions.OandaError(
                  "The instrument.Candles endpoint has returned the following"
                  " error", self.r.json(), status)

    @classmethod
    def to_json(cls, **kwargs):
        """
        An @classmethod that returns the ticker timeseries data that is
        queried.

        Parameters
        ----------
        kwargs
            To accept all keyword arguments that are parsed to the class
            __init__ method.

        Returns
        -------
        dict
            The timeseries data that is returned in the response body of the
            GET request. The data is decoded from json to dic format by the
            requests library.

        See Also
        --------
        Candles.__init__ : The GET HTTP request to the API endpoint.
        Candles.to_dic : The class method that returns the to_json output in a
                         pandas DataFrame.

        Examples
        --------
        >>> from pprint import pprint
        >>> from htp.api.oanda import Candles
        >>> ticker = "EUR_USD"
        >>> arguments = {
        ...     "from": "2019-06-27T17:00:00.000000000Z", "count": "3"}
        >>> pprint(
        ...     Candles.to_json(instrument=ticker, queryParameters=arguments))
        {'candles': [{'complete': True,
                      'mid': {'c': '1.13664',
                              'h': '1.13664',
                              'l': '1.13662',
                              'o': '1.13662'},
                      'time': '2019-06-27T17:00:00.000000000Z',
                      'volume': 2},
                     {'complete': True,
                      'mid': {'c': '1.13662',
                              'h': '1.13662',
                              'l': '1.13662',
                              'o': '1.13662'},
                      'time': '2019-06-27T17:00:05.000000000Z',
                      'volume': 1},
                     {'complete': True,
                      'mid': {'c': '1.13666',
                              'h': '1.13666',
                              'l': '1.13664',
                              'o': '1.13664'},
                      'time': '2019-06-27T17:00:10.000000000Z',
                      'volume': 2}],
         'granularity': 'S5',
         'instrument': 'EUR_USD'}
        """
        try:
            data = cls(**kwargs).r.json()
        except (exceptions.ApiError, exceptions.OandaError) as e:
            logger.exception(e)
            key = (kwargs["queryParameters"]["from"],
                   kwargs["queryParameters"]["to"])
            return {key: e}
        else:
            return data

    @classmethod
    def to_df(cls, filename=None, **kwargs):
        """
        An @classmethod that returns the ticker timeseries data that is
        queried.

        Parameters
        ----------
        filename : str
            The `.csv` filename with path if desired output directory is not
            the current one.
        kwargs
            To accept all keyword arguments that are parsed to the class
            __init__ method.

        Returns
        -------
        pandas.core.frame.DataFrame
            The dic that is returned by the `to_json` class method is further
            manipulated into a pandas DataFrame object.
        csv
            Optional output if a filename is parsed in the arguments. This will
            save the ticker timeseries data in a `.csv` file.

        See Also
        --------
        Candles.__init__ : The GET HTTP request to the API endpoint.
        Candles.to_json : The class method that returns the endpoint response's
                          body in dic format.

        Examples
        --------
        >>> from pprint import pprint
        >>> from htp.api.oanda import Candles
        >>> ticker = "EUR_USD"
        >>> arguments = {
        ...     "from": "2019-06-27T17:00:00.000000000Z", "count": "3"}
        >>> pprint(Candles.to_df(instrument=ticker, queryParameters=arguments))
                                open     high      low    close
        2019-06-27 17:00:00  1.13662  1.13664  1.13662  1.13664
        2019-06-27 17:00:05  1.13662  1.13662  1.13662  1.13662
        2019-06-27 17:00:10  1.13664  1.13666  1.13664  1.13666
        """

        dic = {}

        cols = {"o": "open", "h": "high", "l": "low", "c": "close"}

        resp = cls.to_json(**kwargs)
        if "exc" in resp:
            return None

        price = "".join([i for i in ["mid", "bid", "ask"]
                         if i in resp["candles"][0].keys()])
        for i in range(len(resp["candles"])):
            dic[resp["candles"][i]["time"]] = resp["candles"][i][price]

        data = pd.DataFrame.from_dict(dic, orient="index").rename(columns=cols)
        data_index_dt = data.set_index(
            pd.to_datetime(data.index,
                           format="%Y-%m-%dT%H:%M:%S.%f000Z"), drop=True)
        data_sorted = data_index_dt.sort_index()

        if filename is None:
            return data_sorted
        else:
            return data_sorted.to_csv(filename)


if __name__ == "__main__":
    """
    python htp/api/oanda.py "AUD_JPY" "2018-06-25T16:00:00.000000000Z" 50\
            "M15" out.csv
    """
    logger.enable("__main__")
    logger.add(
        sys.stdout, format="{time} - {level} - {message}", filter="__main__")
    ticker = sys.argv[1]
    queryParameters = {
        "from": sys.argv[2], "count": sys.argv[3], "granularity": sys.argv[4]}
    Candles.to_df(filename=sys.argv[5], instrument=ticker,
                  queryParameters=queryParameters)
