"""A command line script to generate indicator values from select ticker data.
"""
import click
from celery import group
from htp.aux import tasks


def get_data(ticker, price, granularity):

    filename = f"/Users/juleskirk/Documents/tutorials/data/{ticker}.h5"
    key = f"{granularity}/{price}"

    get = tasks.load_data.s(filename, key)

    header = group(
        tasks.set_smooth_moving_average.s(),
        tasks.set_ichimoku_kinko_hyo.s()
        )

    callback = tasks.assemble.s(granularity, filename)

    return (get | header | callback).delay() 
    

@click.command()
@click.argument("ticker", type=click.STRING)
@click.argument("price", type=click.STRING)
@click.argument("granularity", type=click.STRING)
def clickIndicator(ticker, price, granularity):
    return get_data(ticker, price, granularity).get()


if __name__ == '__main__':
    clickIndicator()
