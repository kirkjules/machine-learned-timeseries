import requests
import pandas as pd
from htp import celery
from htp.api import Api
from celery import Task
from htp.api.oanda import Candles


class SessionTask(Task, Api):
    """Base class for celery task function responsible for engaging the api
    endpoint. Designed to establish a session object once at instantiation
    rather the have individual connection created for every celery task on the
    same worker."""
    _s = None
    @property
    def s(self):
        if self._s is None:
            self._s = requests.Session()
            self._s.headers.update(
                {"Content-Type": "application/json",
                 "Authorization": f"Bearer {self.details['token']}"})
        return self._s


@celery.task(base=SessionTask)
def session_get_data(ticker, params={"count": 5, "price": "M"}, timeout=None):
    """Celery task function to engage Oanda instruments.Candles endpoint.

    Paramaters
    ----------
    ticker : str
        Target ticker's symbol.
    params : dict
        Dictionary containing endpoint arguments that specified in the Oanda
        documentation.
    timeout : float {None}
        Set timeout value for production server code so that function doesn't
        block.

    Returns
    -------
    str
        String containing an error's traceback message.
    dict
        The ticker's timeseries data returned by the api endpoint.
    """
    if "price" not in params.keys():
        params["price"] = "M"
    url = f'https://api-fxpractice.oanda.com/v3/instruments/{ticker}/candles?'
    try:
        r = session_get_data.s.get(url, params=params, timeout=timeout)
    except requests.exceptions.RequestException as e:
        return str(e)
    else:
        if r.status_code != requests.codes.ok:
            return (pd.DataFrame(columns=["open", "high", "low", "close"]),
                    (params["price"], params["granularity"], ticker))
        else:
            return (Candles.to_df(r.json(), params),
                    (params["price"], params["granularity"], ticker))


@celery.task
def merge_data(results):
    for result in results:
        if isinstance(result, str):
            results.remove(result)
    if results:
        total = pd.concat([result[0] for result in results])
        price = set([result[1][0] for result in results])
        granularity = set([result[1][1] for result in results])
        ticker = set([result[1][2] for result in results])
        if len(price) == 1:
            filename = f"/Users/juleskirk/Documents/projects/htp/data/{list(ticker)[0]}.h5"
            key = f"{list(granularity)[0]}/{list(price)[0]}"
            print(f"filename: {filename}")
            print(f"key: {key}")
            print(total)
            with pd.HDFStore(filename) as store:
                store.append(key, total)
