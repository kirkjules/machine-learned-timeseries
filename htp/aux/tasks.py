import os
# import sys
import requests
import pandas as pd
from uuid import UUID
from htp import celery
from htp.api import Api
from copy import deepcopy
from celery import Task
from celery.result import AsyncResult
# from datetime import datetime
from htp.api.oanda import Candles
from sqlalchemy import select, MetaData, Table
from htp.aux.database import db_session, engine
from htp.analyse import indicator, evaluate, evaluate_fast, observe
from htp.aux.models import getTickerTask, subTickerTask, indicatorTask,\
        genSignalTask, candles, smoothmovingaverage, ichimokukinkohyo,\
        movavgconvdiv, momentum, stochastic, relativestrengthindex


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
        return (res, params["price"], params["granularity"], self.request.id)


@celery.task(ignore_result=True)
def merge_data(results, ticker, price, granularity, task_id=None):
    """Sort ticker data in chunks to designated lists matching the same ticker,
    price and granularity to be respectively concetenated and bulk inserted
    into the database."""
    d = {}
    for val in price:
        for interval in granularity:
            d[f"{interval}/{val}"] = []

    for result in results:
        if not isinstance(result[0], str):
            d[f"{result[2]}/{result[1]}"].append(deepcopy(result[0]))
        AsyncResult(result[3]).forget()

    for k in d.keys():
        if len(d[k]) > 0:
            df = pd.concat(d[k])
            df = df.loc[~df.index.duplicated(keep='first')]
            df.sort_index(inplace=True)
            df.reset_index(inplace=True)
            df.rename(columns={'index': 'timestamp'}, inplace=True)
            save_data(df, candles, getTickerTask, ('status',), task_id[f'{k}'])


def load_data(task_id, model, columns):
    _id = str(task_id)
    metadata = MetaData(bind=None)
    table = Table(model, metadata, autoload=True, autoload_with=engine)
    stmt = select([getattr(table.c, col) for col in columns]).where(
        table.columns.batch_id == _id)
    df = pd.read_sql(
        stmt, engine, index_col='timestamp', parse_dates=['timestamp'],
        columns=columns)
    return df


def save_data(df, data_table, record_table, record_columns, task_id):
    """Helper function to record tasks' internal functions' success in the
    database."""
    df['batch_id'] = task_id
    rows = df.to_dict('records')
    db_session.bulk_insert_mappings(data_table, rows)
    del rows

    entry = db_session.query(record_table).get(task_id)
    for col in record_columns:
        setattr(entry, col, 1)
    db_session.commit()
    db_session.remove()


@celery.task(ignore_result=True)
def set_smooth_moving_average(task_id):
    df = load_data(
        task_id, 'candles', ['timestamp', 'open', 'high', 'low', 'close'])
    periods = [3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 15, 16, 20, 24, 25, 28, 30, 32,
               35, 36, 40, 48, 50, 60, 64, 70, 72, 80, 90, 96, 100]
    avgs = []
    for i in periods:
        avg = indicator.smooth_moving_average(df, column="close",
                                              period=i)
        avgs.append(avg)

    r = pd.concat(avgs, axis=1)
    r.reset_index(inplace=True)
    save_data(r, smoothmovingaverage, indicatorTask, ('sma_status',), task_id)


@celery.task(ignore_result=True)
def set_ichimoku_kinko_hyo(task_id):
    df = load_data(
        task_id, 'candles', ['timestamp', 'open', 'high', 'low', 'close'])
    r = indicator.ichimoku_kinko_hyo(df)
    r.reset_index(inplace=True)
    save_data(
        r, ichimokukinkohyo, indicatorTask, ('ichimoku_status',), task_id)


@celery.task(ignore_result=True)
def set_moving_average_convergence_divergence(task_id):
    df = load_data(
        task_id, 'candles', ['timestamp', 'open', 'high', 'low', 'close'])
    macd = indicator.moving_average_convergence_divergence(df)
    macd.reset_index(inplace=True)
    save_data(macd, movavgconvdiv, indicatorTask, ('macd_status',), task_id)


@celery.task(ignore_result=True)
def set_stochastic(task_id):
    df = load_data(
        task_id, 'candles', ['timestamp', 'open', 'high', 'low', 'close'])
    stoch = indicator.stochastic(df)
    stoch.reset_index(inplace=True)
    save_data(
        stoch, stochastic, indicatorTask, ('stochastic_status',), task_id)


@celery.task(ignore_result=True)
def set_relative_strength_index(task_id):
    df = load_data(
        task_id, 'candles', ['timestamp', 'open', 'high', 'low', 'close'])
    rsi = indicator.relative_strength_index(df)
    rsi.reset_index(inplace=True)
    save_data(
        rsi, relativestrengthindex, indicatorTask, ('rsi_status',), task_id)


@celery.task(ignore_result=True)
def set_momentum(task_id):
    df = load_data(
        task_id, 'candles', ['timestamp', 'open', 'high', 'low', 'close'])
    atr = indicator.Momentum.average_true_range(df)
    adx = indicator.Momentum.average_directional_movement(df)
    r = atr.merge(adx, how="left", left_index=True, right_index=True,
                  validate="1:1")
    r.reset_index(inplace=True)
    save_data(
        r, momentum, indicatorTask, ('atr_status', 'adx_status'), task_id)


@celery.task
def load_signal_data(data):
    d = {}
    for files in data:
        with pd.HDFStore(files[0]) as store:  # filename
            d[files[2]] = store[files[1]]  # key

    sma = [s for s in d['target'].columns if "close_sma_" in s]
    d['sys'] = d['target'][sma].copy()

    d['target']['iky_cat'] = d['target'][
        ['tenkan', 'kijun', 'senkou_A', 'senkou_B']].apply(
            evaluate.iky_cat, axis=1)

    i = ['%K', '%D', 'RSI', 'MACD', 'Signal', 'Histogram', 'ADX', 'ATR',
         'iky_cat']
    prop = d['target'][i].copy()
    del d['target']
    if 'sup' in d.keys():
        d['sup']['iky_cat'] = d['sup'][
            ['tenkan', 'kijun', 'senkou_A', 'senkou_B']].apply(
                evaluate.iky_cat, axis=1)
        sup_prop = d['sup'][i].copy()
        del d['sup']
        prop = prop.merge(
            sup_prop, how="left", left_index=True, right_index=True,
            suffixes=("_target", "_sup"))
        prop.fillna(method="ffill", inplace=True)
    else:
        cols = {}
        for label in i:
            cols[label] = f"{label}_target"
        prop.rename(columns=cols, inplace=True)

    d['prop'] = prop
    return d
    # testing
    # print(sys.getsizeof(d))
    # for i in d.keys():
    #     print(f"{i}: {len(d[i])}")
    #     print(d[i].columns)


@celery.task(ignore_result=True)
def gen_signals(task_id, fast, slow, trade, atr_multiplier):

    price = {'buy': {'entry': data['A'], 'exit': data['B']},
             'sell': {'entry': data['B'], 'exit': data['A']}}

    if 'JPY' in ticker:
        exp = 3
    else:
        exp = 5

    atr = load_data(task_id, 'momentum', ['timestamp', 'atr']).dropna()
    mid_close = load_data(task_id, 'candles', ['timestamp', 'close'])

    sys_signals = evaluate_fast.Signals.atr_stop_signals(
        ATR, data['M'], price[trade]['entry'], price[trade]['exit'], data_sys,
        fast, slow, multiplier=atr_multiplier, trade=trade, exp=exp)

    save_data(sys_signals)

    # close_to_close = observe.close_in_atr(data['M'], ATR)
    # close_to_fast_signal = observe.close_to_signal_by_atr(
    #     data['M'], data_sys, fast, ATR)
    # close_to_slow_signal = observe.close_to_signal_by_atr(
    #     data['M'], data_sys, slow, ATR)

    # properties = pd.concat([data['prop'], close_to_close, close_to_fast_signal,
    #                        close_to_slow_signal], axis=1)
    # properties = properties.shift(1)  # very important, match most recent known
    # property to proceeding timestamp where trade is entered.
    # for s in properties.columns:
    #     if "ATR_" in s:
    #         properties.drop([s], axis=1, inplace=True)

    # signals_with_properties = sys_signals.merge(
    #     properties, how="inner", left_on="entry_datetime", right_index=True,
    #     validate="1:1")

    # signals_with_properties["close_in_atr"] = pd.to_numeric(
    #     signals_with_properties["close_in_atr"], errors="coerce",
    #     downcast='integer')

    # converts values from decimal objects into float32 and then float64 to
    # round.
    # for col in ["exit_price", "stop_loss"]:
    #     signals_with_properties[col] = pd.to_numeric(
    #         signals_with_properties[col], errors="coerce",
    #         downcast='float').astype(float)

    # signals_with_properties = signals_with_properties.round(
    #     {"entry_price": exp, "exit_price": exp, "stop_loss": exp})

    # path = f"/Users/juleskirk/Documents/projects/htp/data/{ticker}/\
    # {granularity}/signals"
    # if not os.path.isdir(path):
    #     os.mkdir(path)

    # signals_with_properties.to_hdf(
    #     f"{path}/{trade}-{fast}-{slow}.h5", 'S',  mode='w', format='table',
    #     complevel=9)

    # record(genSignalTask, ('status',), task_id=task_id)
