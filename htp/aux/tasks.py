import requests
import pandas as pd
from htp import celery
from htp.api import Api
from celery import Task
from datetime import datetime
from htp.analyse import indicator
from htp.api.oanda import Candles
from htp.aux.database import db_session
from htp.aux.models import CandlesTasks


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


@celery.task(base=SessionTask, bind=True)
def session_get_data(
  self, ticker, params={"count": 5, "price": "M"}, timeout=None):
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
    res = None
    if "price" not in params.keys():
        params["price"] = "M"
    url = f'https://api-fxpractice.oanda.com/v3/instruments/{ticker}/candles?'
    try:
        r = session_get_data.s.get(url, params=params, timeout=timeout)
    except requests.exceptions.RequestException as e:
        res = str(e)
    else:
        if r.status_code != requests.codes.ok:
            res = str(r.json()["errorMessage"])
        else:
            res = Candles.to_df(r.json(), params)
    finally:
        params["to"] = datetime.strptime(
            params["to"], "%Y-%m-%dT%H:%M:%S.%f000Z")
        params["from"] = datetime.strptime(
            params["from"], "%Y-%m-%dT%H:%M:%S.%f000Z")
        entry = CandlesTasks(
            ticker=ticker, from_=params["from"], to=params["to"],
            granularity=params["granularity"], price=params["price"],
            task_id=self.request.id)
        if isinstance(res, str):
            entry.task_error = res
        db_session.add(entry)
        db_session.commit()
        db_session.remove()
        return res


@celery.task
def merge_data(results, price, granularity, ticker):
    for result in results:
        if isinstance(result, str):
            results.remove(result)
    if results:
        total = pd.concat([result for result in results])
        total = total[~total.index.duplicated(keep='first')]
        total.sort_index(inplace=True)
        filename = f"/Users/juleskirk/Documents/projects/htp/data/{ticker}.h5"
        with pd.HDFStore(filename) as store:
            store.append(f"{granularity}/{price}", total)


@celery.task
def load_data(filename, key):
    with pd.HDFStore(filename) as store:
        return store[key]


@celery.task
def set_smooth_moving_average(df):
    periods = [3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 15, 16, 20, 24, 25, 28, 30, 32,
               35, 36, 40, 48, 50, 60, 64, 70, 72, 80, 90, 96, 100]
    avgs = []
    for i in periods:
        avg = indicator.smooth_moving_average(df, column="close", period=i)
        avgs.append(avg)
    return pd.concat(avgs, axis=1)


@celery.task
def set_ichimoku_kinko_hyo(df):
    return indicator.ichimoku_kinko_hyo(df)


@celery.task
def assemble(list_indicators, granularity, filename):
    indicators = pd.concat(list_indicators, axis=1)
    with pd.HDFStore(filename) as store:
        store.append(f"{granularity}/indicators", indicators)
