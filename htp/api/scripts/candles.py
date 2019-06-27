"""A command line script to query ticker data directly from the oanda api.

E.g. candles "data/AUD_JPYH120180403-c100.csv" "AUD_JPY" --granularity "H1"
--from "2018-04-03 22:00:00" --count 100
"""
import click
from htp.api import oanda


def fmt(date):
    if date is not None:
        str_ = date.strftime("%Y-%m-%dT%H:%M:%S.%f000Z")
        return str_


@click.command()
@click.argument("filename", type=click.STRING)
@click.argument("ticker", type=click.STRING)
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
              granularity will determine the number of candlesticks to\
              return.")
@click.option("--from", "-f", "from_",
              default=None,
              type=click.DateTime(formats=None),
              help="The start of the time range to fetch candlesticks for.")
@click.option("--to",
              default=None,
              type=click.DateTime(formats=None),
              help="The end of the time range to fetch candlesticks for.")
@click.option("--smooth",
              default=False,
              type=click.BOOL,
              help="A flag that controls whether the candlestick is\
              “smoothed” or not. A smoothed candlestick uses the previous\
              candle’s close price as its open price, while an unsmoothed\
              candlestick uses the first price from its time range as its\
              open price.")
@click.option("--includefirst",
              default=True,
              type=click.BOOL,
              help="A flag that controls whether the candlestick that is\
              covered by the from time should be included in the results.\
              This flag enables clients to use the timestamp of the last\
              completed candlestick received to poll for future candlesticks\
              but avoid receiving the previous candlestick repeatedly.")
@click.option("--dailyalignment",
              default=17,
              type=click.IntRange(0, 23, clamp=True),
              help="The hour of the day (in the specified timezone) to use\
              for granularities that have daily alignments.")
@click.option("--weeklyalignment",
              default="Friday",
              type=click.STRING,
              help="The day of the week used for granularities that have\
              weekly alignment.")
@click.option("--alignmenttimezone",
              default="America/New_York",
              type=click.STRING,
              help="The timezone to use for the dailyAlignment parameter.\
              Candlesticks with daily alignment will be aligned to the\
              dailyAlignment hour within the alignmentTimezone. Note that\
              the returned times will still be represented in UTC.")
def clickData(filename, ticker, price, granularity, count, from_, to, smooth,
              includefirst, dailyalignment, weeklyalignment,
              alignmenttimezone):

    arguments = {"price": price,
                 "granularity": granularity,
                 "count": count,
                 "from": fmt(from_),
                 "to": fmt(to),
                 "smooth": smooth,
                 "includeFirst": includefirst,
                 "dailyAlignment": dailyalignment,
                 "alignmentTimezone": alignmenttimezone,
                 "weeklyAlignment": weeklyalignment}

    if from_ is None:
        del arguments["from"]
        del arguments["to"]
        del arguments["includeFirst"]
    else:
        del arguments["count"]

    oanda.Candles.to_df(filename=filename,
                        **{"instrument": ticker, "queryParameters": arguments})
    click.echo("Download complete")
