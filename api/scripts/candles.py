import click
from api import oanda


@click.command()
@click.option("--price",
              default="M",
              type=click.STRING,
              help="The Price components to get candlestick data for.\
              Can contain any combination of the characters M midpoint\
              candles B bid candles and A ask candles")
@click.option("--granularity",
              default="S5",
              type=click.STRING,
              help="The granularity of the candlesticks to fetch")
@click.option("--count",
              default="500",
              type=click.IntRange(500, 5000, clamp=True),
              help="The number of candlesticks to return in the reponse.\
              Count should not be specified if both the start and end\
              parameters are provided, as the time range combined with the\
              graularity will determine the number of candlesticks to\
              return.")
@click.option("--from",
              type=click.DateTime(formats="%Y-%m-%dT%H:%M:%SZ"),
              help="The start of the time range to fetch candlesticks for.")
@click.option("--to",
              type=click.DateTime(formats="%Y-%m-%dT%H:%M:%SZ"),
              help="The end of the time range to fetch candlesticks for.")
@click.option("--smooth",
              default=False,
              type=click.BOOL,
              help="A flag that controls whether the candlestick is\
              “smoothed” or not. A smoothed candlestick uses the previous\
              candle’s close price as its open price, while an unsmoothed\
              candlestick uses the first price from its time range as its\
              open price.")
@click.option("--includeFirst",
              default=True,
              type=click.BOOL,
              help="")
@click.option("--dailyAlignment",
              default=17,
              type=click.IntRange(0, 23, clamp=True),
              help="")
@click.option("--weeklyAlignment",
              default="Friday",
              type=click.STRING,
              help="")
def clickData(ticker, price, granularity, count, from, to, smooth,
              includeFirst, dailyAlignment, alignmentTimezone,
              weeklyAlignment):

    ticker = "EUR_USD"
    arguments = {"count": "6", "price": "M", "granularity": "S5"}
    r = oanda.Instrument("api/config.ini")
    data = r.candles(ticker, arguments)
    click.echo(data.json())


if __name__ == '__main__':
    clickData()
