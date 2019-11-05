"""A command line script to generate indicator values from select ticker data.
"""
import click
import pandas as pd
from celery import Celery, chord
from htp.analyse import indicator


app = Celery('apply', broker='redis://localhost', backend='redis://localhost')
app.conf.accept_content = ['pickle']
app.conf.task_serializer = 'pickle'
app.conf.result_serializer = 'pickle'


@app.task
def set_smooth_moving_average(df):
    periods = [3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 15, 16, 20, 24, 25, 28, 30, 32,
               35, 36, 40, 48, 50, 60, 64, 70, 72, 80, 90, 96, 100]
    avgs = []
    for i in periods:
        avg = indicator.smooth_moving_average(df, column="close", period=i)
        avgs.append(avg)
    sma_x_y = pd.concat(avgs, axis=1)
    sma_x_y.to_csv("data/celery_sma.csv")
    return sma_x_y


@app.task
def set_ichimoku_kinko_hyo(df):
    ichimoku = indicator.ichimoku_kinko_hyo(df)
    ichimoku.to_csv("data/celery_ichimoku.csv")
    return ichimoku


@app.task
def assemble(list_df):
    indicators = pd.concat(list_df, axis=0)
    indicators.to_csv("data/celery_indicators.csv")


@click.command()
@click.argument("ticker", type=click.STRING)
@click.argument("granularity", type=click.STRING)
def clickIndicator(ticker, granularity):
    with pd.HDFStore(f"data/{ticker}.h5") as store:
        df = store[f"{granularity}/M"]

    chord([set_smooth_moving_average.s(df),
           set_ichimoku_kinko_hyo.s(df)])(assemble.s())
