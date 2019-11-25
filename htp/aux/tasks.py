import requests
import pandas as pd
from uuid import UUID
from htp import celery
from htp.api import Api
from celery import Task
# from datetime import datetime
from htp.analyse import indicator
from htp.api.oanda import Candles
from htp.aux.database import db_session
from htp.aux.models import getTickerTask, subTickerTask, indicatorTask


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
  self, ticker, params={"count": 5, "price": "M"}, timeout=None, db=False):
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
    db : boolean
        Flag to indicate if function progress to be tracked in the database.

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
        if db:
            entry = db_session.query(subTickerTask).get(UUID(self.request.id))
            if isinstance(res, str):
                entry.status = 0
                entry.error = res
            else:
                entry.status = 1
            db_session.commit()
            db_session.remove()
        return (res, params["price"], params["granularity"])


def record(table, columns, task_id=None):
    """Helper function to record tasks' internal functions' success in the
    database."""
    if task_id is not None:
        entry = db_session.query(table).get(task_id)
        for column in columns:
            setattr(entry, column, 1)
        db_session.commit()
        db_session.remove()
    else:
        pass


@celery.task
def merge_data(results, ticker, price, granularity, task_id=None):

    d = {}
    for val in price:
        for interval in granularity:
            # print(f"{interval}/{val}")
            d[f"{interval}/{val}"] = []

    for result in results:
        if not isinstance(result[0], str):
            # params["granularity"]/params["price"]
            d[f"{result[2]}/{result[1]}"].append(result[0])

    for k in d.keys():
        if len(d[k]) > 0:
            total = pd.concat(d[k])
            total = total.loc[~total.index.duplicated(keep='first')]
            total.sort_index(inplace=True)

            filename = f"/Users/juleskirk/Documents/projects/htp/data/\
{ticker}{k.split('/')[0]}.h5"

            with pd.HDFStore(filename) as store:
                # to maximise storage:
                # $ ptrepack --chunkshape=auto --propindexes --complevel=9
                # data/NZD_JPY.h5 data/out.h5
                # to prevent duplicates
                if f"/{k.split('/')[1]}" in store.keys():
                    # print("Removing data")
                    store.remove(f"{k.split('/')[1]}")
                store.put(f"{k.split('/')[1]}", total)

            del total
            record(getTickerTask, ('status',), task_id=task_id[f"{k}"])


@celery.task
def load_data(filename, key):
    with pd.HDFStore(filename) as store:
        return store[key]


@celery.task
def set_smooth_moving_average(df, task_id=None):
    periods = [3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 15, 16, 20, 24, 25, 28, 30, 32,
               35, 36, 40, 48, 50, 60, 64, 70, 72, 80, 90, 96, 100]
    avgs = []
    for i in periods:
        avg = indicator.smooth_moving_average(df, column="close", period=i)
        avgs.append(avg)

    r = pd.concat(avgs, axis=1)
    record(indicatorTask, ('sma_status',), task_id=task_id)
    return r


@celery.task
def set_ichimoku_kinko_hyo(df, task_id=None):
    r = indicator.ichimoku_kinko_hyo(df)
    record(indicatorTask, ('ichimoku_status',), task_id=task_id)
    return r


@celery.task
def set_moving_average_convergence_divergence(df, task_id=None):
    macd = indicator.moving_average_convergence_divergence(df)
    macd.drop(['emaF', 'emaS'], axis=1, inplace=True)
    record(indicatorTask, ('macd_status',), task_id=task_id)
    return macd


@celery.task
def set_stochastic(df, task_id=None):
    stoch = indicator.stochastic(df)
    stoch.drop(['close', 'minN', 'maxN'], axis=1, inplace=True)
    record(indicatorTask, ('stochastic_status',), task_id=task_id)
    return stoch


@celery.task
def set_relative_strength_index(df, task_id=None):
    rsi = indicator.relative_strength_index(df)
    rsi.drop(['avg_gain', 'avg_loss', 'RS'], axis=1, inplace=True)
    record(indicatorTask, ('rsi_status',), task_id=task_id)
    return rsi


@celery.task
def set_momentum(df, task_id=None):
    atr = indicator.Momentum.average_true_range(df)
    atr.drop(['HL', 'HpC', 'LpC', 'TR', 'r14TR'], axis=1, inplace=True)
    adx = indicator.Momentum.average_directional_movement(df)
    adx.drop(['+DI', '-DI', 'DX'], axis=1, inplace=True)
    r = atr.merge(adx, how="left", left_index=True, right_index=True,
                  validate="1:1")
    record(indicatorTask, ('atr_status', 'adx_status'), task_id=task_id)
    return r


@celery.task
def assemble(list_indicators, ticker, granularity, task_id=None):
    indicators = pd.concat(list_indicators, axis=1)
    filename = f"/Users/juleskirk/Documents/projects/htp/data/\
{ticker}{granularity}indicators.h5"
    indicators.to_hdf(filename, 'I',  mode='w', format='fixed', complevel=9)
    record(indicatorTask, ('status',), task_id=task_id)
