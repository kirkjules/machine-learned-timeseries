"""
The oanda module contains functions that interact with the Oanda V20 API
endpoints, docummented at http://developer.oanda.com/rest-live-v20/introduction
"""
import logging
import requests
import pandas as pd
from htp.api import Api, exceptions

log = logging.getLogger(__name__)


class Candles(Api):
    """
    A request operation that queries the Oanda instrument.Candles endpoint for
    ticker timeseries data.

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
    queryParameters : dic
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

    OandaException
        If the response status code is not 200. Here, the endpoint has provided
        a reason in the in the response body and this exposed by the exception.
        An example case is where the authorization token is incorrect.

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

    See Also
    --------
    htp.api : Api
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
            exc = exceptions.ApiError("There has been an error connecting"
                                      " with the api endpoint as raised by: "
                                      " {}".format(e))
            log.info(exc)
            raise exc from None
        else:
            self.status = self.r.status_code

            if self.r.status_code != 200:
                raise exceptions.OandaError(
                  "The instrument.Candles endpoint has returned the following"
                  " error",
                  self.r.json(),
                  status_code=self.r.status_code)

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
        dic
            The timeseries data that is returned in the response body of the
            GET request. The data is decoded from json to dic format by the
            requests library.

        See Also
        --------
        Candles.__init__ : The GET HTTP request to the API endpoint.
        Candles.to_dic : The class method that returns the to_json output in a
                         pandas DataFrame.
        """
        return cls(**kwargs).r.json()

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
        pandas.DataFrame
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
        """

        dic = {}

        cols = {"o": "open", "h": "high", "l": "low", "c": "close"}

        resp = cls.to_json(**kwargs)
        for i in range(len(resp["candles"])):
            dic[resp["candles"][i]["time"]] = resp["candles"][i]["mid"]

        data = pd.DataFrame.from_dict(dic, orient="index").rename(columns=cols)

        if filename is None:
            return data
        else:
            return data.to_csv(filename)


if __name__ == "__main__":

    import os
    from pprint import pprint

    ticker = "EUR_USD"
    arguments = {"count": "6", "price": "M", "granularity": "S5"}
    cf = os.path.join(os.path.dirname(__file__), "../..", "config.yaml")
    data = Candles(configFile=cf, instrument=ticker, queryParameters=arguments)
    pprint(data.r.json())
    pprint(Candles.to_json(configFile=cf, instrument=ticker,
                           queryParameters=arguments))
    pprint(Candles.to_df(configFile=cf, instrument=ticker,
                         queryParameters=arguments))
