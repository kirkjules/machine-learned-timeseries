# import sys
from pprint import pprint
from loguru import logger
from htp.api.oanda import Candles

logger.enable("htp.api.oanda")
# logger.add(sys.stdout, format="{time} - {level} - {message}")

data = Candles.to_df(
    instrument="AUD_JPY", queryParameters={
        "from": "2019-07-05T22:00:00.000000000Z", "count": 10, "granularity":
        "D"})
pprint(data)
