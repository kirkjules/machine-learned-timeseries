import requests
import numpy as np
import pandas as pd
from uuid import UUID, uuid4
from htp import celery
from htp.api import Api
from copy import deepcopy
from celery import Task
from celery.result import AsyncResult
from htp.api import oanda
from htp.toolbox import calculator
from sqlalchemy import select, MetaData, Table
from htp.aux.database import db_session, engine
from htp.analyse import indicator, evaluate_fast, observe, machine_learn
from htp.aux.models import GetTickerTask, SubTickerTask, IndicatorTask,\
        GenSignalTask, Candles, moving_average, Signals, Results


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
def session_get_data(self, ticker, params={"count": 5, "price": "M"},
                     timeout=None):
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
    pandas.core.frame.DataFrame
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
            res = oanda.Candles.to_df(r.json(), params)
    finally:
        entry = db_session.query(SubTickerTask).get(UUID(self.request.id))
        if isinstance(res, str):
            entry.status = 0
            entry.error = res
        else:
            entry.status = 1
        db_session.commit()
        db_session.remove()
    return (res, self.request.id)


@celery.task(ignore_result=True)
def merge_data(results, ticker, price, granularity, task_id=None):
    """Sort ticker data in chunks to designated lists matching the same ticker,
    price and granularity to be respectively concetenated and bulk inserted
    into the database."""
    dfs = []
    for result in results:
        if not isinstance(result[0], str):
            dfs.append(deepcopy(result[0]))
        AsyncResult(result[3]).forget()

    if len(dfs) > 0:
        df = pd.concat(dfs)
        df = df.loc[~df.index.duplicated(keep='first')]
        df.sort_index(inplace=True)
        df.reset_index(inplace=True)
        df.rename(columns={'index': 'timestamp'}, inplace=True)
        save_data(df, Candles, GetTickerTask, ('status',), task_id)


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


def load_data(task_id, model, columns, index_col='timestamp',
              dates_cols=['timestamp']):
    _id = str(task_id)
    metadata = MetaData(bind=None)
    table = Table(model, metadata, autoload=True, autoload_with=engine)
    stmt = select([getattr(table.c, col) for col in columns]).where(
        table.columns.batch_id == _id)
    df = pd.read_sql(stmt, engine, index_col=index_col, parse_dates=dates_cols,
                     columns=columns)
    df.sort_index(inplace=True)
    return df


@celery.task(ignore_result=True)
def set_indicator(task_id, func, table, task_cols, target=None, shift=-1):
    df_indicate = load_data(
        task_id, 'candles', ['timestamp', 'open', 'high', 'low', 'close'])
    df = func(df_indicate)

    if target:
        df_target = load_data(
            target, 'candles', ['timestamp', 'open', 'high', 'low', 'close'])
        df_merge = df_target.merge(
            df, how='left', left_index=True, right_index=True, validate='1:1')
        df_merge.drop(['open', 'high', 'low', 'close'], axis=1, inplace=True)
        df_merge.fillna(method='ffill', inplace=True)
    else:
        df_merge = df.copy()

    df_merge.reset_index(inplace=True)
    df_merge['timestamp_shift'] = df_merge['timestamp'].shift(shift)
    df_merge.dropna(subset=['timestamp_shift'], axis=0, inplace=True)

    save_data(df_merge, table, IndicatorTask, task_cols,  task_id)


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
    save_data(r, moving_average, IndicatorTask, ('sma_status',), task_id)


@celery.task(ignore_result=True)
def gen_signals(mid_id, ask_id, bid_id, fast, slow, trade, multiplier=6.0):

    price = {'buy': {'entry': ask_id, 'exit': bid_id},
             'sell': {'entry': bid_id, 'exit': ask_id}}
    mid_close = load_data(mid_id, 'candles', ['timestamp', 'close'])
    entry = load_data(price[trade]['entry'], 'candles', ['timestamp', 'open'])
    entry.rename(columns={'open': 'entry_open'}, inplace=True)
    exit_ = load_data(
        price[trade]['exit'], 'candles', ['timestamp', 'open', 'high', 'low'])
    exit_.rename(
        columns={'open': 'exit_open', 'high': 'exit_high', 'low': 'exit_low'},
        inplace=True)
    atr = load_data(mid_id, 'momentum', ['timestamp', 'atr'])
    dfsys = load_data(mid_id, 'moving_average', ['timestamp', fast, slow])
    df = pd.concat([mid_close, entry, exit_, atr, dfsys], axis=1)
    df.dropna(inplace=True)

    sys_signals = evaluate_fast.Signals.atr_stop_signals(
        df, fast, slow, multiplier=multiplier, trade=trade)

    close_to_close = observe.close_in_atr(mid_close, atr)
    close_to_fast_signal = observe.close_to_signal_by_atr(
        mid_close, dfsys, fast, atr)
    close_to_slow_signal = observe.close_to_signal_by_atr(
        mid_close, dfsys, slow, atr, speed='slow')
    obs = pd.concat(
        [close_to_close, close_to_fast_signal, close_to_slow_signal], axis=1)
    obs_shift = obs.shift(1)
    sys_signals = sys_signals.merge(
        obs_shift, how='left', left_on='entry_datetime', right_index=True,
        validate='1:1')

    sys_signals.dropna(inplace=True)
    sys_signals.drop(
        sys_signals[sys_signals['stop_loss'] <= 0].index, inplace=True)

    sys_entry = db_session.query(GenSignalTask).filter(
        GenSignalTask.batch_id == mid_id, GenSignalTask.fast == fast,
        GenSignalTask.slow == slow, GenSignalTask.trade_direction == trade,
        GenSignalTask.exit_strategy == f'trailing_atr_{multiplier}').first()
    if sys_entry is None:
        sys_id = uuid4()
        db_session.add(GenSignalTask(
            id=sys_id, batch_id=mid_id, fast=fast, slow=slow,
            trade_direction=trade, exit_strategy=f'trailing_atr_{multiplier}',
            signal_count=len(sys_signals)))
    else:
        sys_id = sys_entry.id
        setattr(Signals, 'status', 0)
        db_session.query(Signals).filter(Signals.batch_id == sys_id).delete(
            synchronize_session=False)
    db_session.commit()
    save_data(sys_signals, Signals, GenSignalTask, ('status',), sys_id)


@celery.task(bind=True)
def prep_signals(self, prev_id, table, targets, batch_id, sys_id,
                 property_type):

    if prev_id is not None:
        AsyncResult(prev_id).forget()

    for s, d in db_session.query(Signals, table).\
            join(table, Signals.entry_datetime == table.timestamp_shift).\
            filter(table.batch_id == batch_id).\
            filter(Signals.batch_id == sys_id).all():
        for target in targets:
            setattr(s, f'{property_type}_{target}', getattr(d, target))

    db_session.commit()
    return self.request.id


@celery.task(bind=True)
def conv_price(self, prev_id, signal_join_column, signal_target_column,
               conv_batch_id, sys_id):

    if prev_id is not None:
        AsyncResult(prev_id).forget()

    if not conv_batch_id:
        for r in db_session.query(Signals).\
                 filter(Signals.batch_id == sys_id).all():
            if signal_target_column == 'conv_entry_price':
                r.conv_entry_price = r.entry_price
            elif signal_target_column == 'conv_exit_price':
                r.conv_exit_price = r.exit_price
    else:
        for u, a in db_session.query(Signals, Candles.open).\
                join(Candles, getattr(Signals, signal_join_column) ==
                     Candles.timestamp).\
                filter(Candles.batch_id == conv_batch_id).\
                filter(Signals.batch_id == sys_id).all():
            setattr(u, signal_target_column, a)

    db_session.commit()
    return self.request.id


@celery.task(ignore_result=True)
def setup_predict(ticker, granularity, fast, slow, direction, multiplier):
    entry = db_session.query(GetTickerTask).filter(
        GetTickerTask.ticker == ticker, GetTickerTask.granularity ==
        granularity, GetTickerTask.price == 'M').first()

    sys = db_session.query(GenSignalTask).filter(
        GenSignalTask.batch_id == entry.id, GenSignalTask.fast == fast,
        GenSignalTask.slow == slow, GenSignalTask.trade_direction == direction,
        GenSignalTask.exit_strategy == f'trailing_atr_{multiplier}').first()

    db_session.query(Results).filter(
        Results.batch_id == sys.id).delete(synchronize_session=False)

    db_session.commit()

    train_sample_size = 500
    test_sample_size = 50
    num_chunks = ((sys.signal_count - train_sample_size - test_sample_size) /
                  test_sample_size) + 2
    chunks = []
    for ind in range(int(num_chunks)):
        chunks.append(
            (ind * test_sample_size,
             ind * test_sample_size + train_sample_size + test_sample_size))

    for i in chunks:
        action_predict.delay(sys.id, i, ticker, direction, train_sample_size)


@celery.task(ignore_result=True)
def action_predict(sys_id, chunk, ticker, direction, train_sample_size):
    sys_data = load_data(
        sys_id, 'signals',
        ['entry_datetime', 'entry_price', 'stop_loss', 'exit_datetime',
         'exit_price', 'conv_entry_price', 'conv_exit_price', 'target_percK',
         'target_percD', 'target_macd', 'target_signal', 'target_histogram',
         'target_rsi', 'target_adx', 'target_iky_cat', 'sup_percK',
         'sup_percD', 'sup_macd', 'sup_signal', 'sup_histogram', 'sup_rsi',
         'sup_adx', 'sup_iky_cat', 'close_in_atr', 'close_to_fast_by_atr',
         'close_to_slow_by_atr'], index_col='entry_datetime', dates_cols=[
             'entry_datetime', 'exit_datetime'])

    for col in ['conv_entry_price', 'conv_exit_price']:
        sys_data[col].fillna(method='ffill', inplace=True)
        sys_data[col].fillna(method='bfill', inplace=True)

    sys_data.fillna(0, inplace=True)
    sys_data.reset_index(inplace=True)
    data = sys_data.iloc[chunk[0]:chunk[1]].copy()

    results = calculator.count(
        data, ticker, 1000, 0.01, direction, conv=True)
    performance = calculator.performance_stats(results[0:train_sample_size])
    if performance['win_%'] < 20.:  # increased from 20.
        return None

    results["win_loss"] = np.where(results["PL_AUD"] > 0, 1, 0)
    model_data = results.drop(
        ['entry_price', 'stop_loss', 'exit_datetime', 'exit_price',
         'conv_entry_price', 'conv_exit_price', 'PL_PIPS', 'POS_SIZE',
         'PL_AUD', 'PL_REALISED'], axis=1).copy()

    model_data.set_index('entry_datetime', inplace=True)

    prediction_results, win_rate, all_feature_score, top_feature_score =\
        machine_learn.predict(model_data, train_sample_size)

    if prediction_results is not None:

        prediction_en_ex = sys_data[sys_data["entry_datetime"].isin(
            prediction_results.index)].copy()
        prediction_en_ex.reset_index(drop=True, inplace=True)
        live_results = calculator.count(
            prediction_en_ex, ticker, 1000, 0.01, direction, conv=True)

        live_results['batch_id'] = sys_id
        upload = live_results[[
            'batch_id', 'exit_datetime', 'PL_PIPS', 'POS_SIZE', 'PL_AUD',
            'PL_REALISED']].copy()

        rows = upload.to_dict('records')
        db_session.bulk_insert_mappings(Results, rows)
        db_session.commit()
        db_session.close()

    return None


# performance = calculator.performance_stats(live_results)
