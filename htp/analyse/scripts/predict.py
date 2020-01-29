# parse:
# system to be read in (ticker, interval, fast, slow, direction)
# look up conversion ticker and read in if applicable (table in calculator
# module).
# merge conversion open value onto signal dataset for entry and exit.

import numpy as np
from htp.toolbox import calculator
from htp.aux.database import db_session
# from htp.analyse.machine_learn import predict
from htp.analyse.scripts.evaluate import parts
from htp.aux.tasks import prep_signals, conv_price
from htp.aux.models import getTickerTask, genSignalTask,\
        stochastic, convergence_divergence, ichimoku, relative_strength,\
        momentum

# pd.set_option("display.max_columns", 35)
# pd.set_option('max_colwidth', 150)
# pd.set_option("display.max_rows", 50)

# amount = 1000
# RISK_PERC = 0.01
# ticker = 'EUR_USD'
# conv = True
# interval = 'H1'
# fast = 4
# slow = 24
# trade_direction = 'sell'
# train_sample_size = 500
# test_sample_size = 50

# results = data
# num_chunks = ((len(results) - train_sample_size - test_sample_size) /
#               test_sample_size) + 2

# chunks = []
# for ind in range(int(num_chunks)):
    # chunks.append((ind * 100, ind * 100 + 499))
#     chunks.append(
#         (ind * test_sample_size, ind * test_sample_size +
#          train_sample_size + test_sample_size))


def predict_by_chunk(data, start, end, ticker, amount, RISK_PERC, direction,
                     conv=False):
    sub_data = data.iloc[start:end].copy()
    results = calculator.count(
        sub_data, ticker, amount, RISK_PERC, direction, conv=conv)
    # performance = calculator.performance_stats(results)
    # if performance["win_%"] > 20.:
    results["win_loss"] = np.where(results["P/L AUD"] > 0, 1, 0)
    temp = results.loc[:, [
        'entry_datetime', 'win_loss', '%K_target', '%D_target', 'RSI_target',
        'MACD_target', 'Signal_target', 'Histogram_target', 'ADX_target',
        'iky_cat_target', '%K_sup', '%D_sup', 'RSI_sup', 'MACD_sup',
        'Signal_sup', 'Histogram_sup', 'ADX_sup', 'iky_cat_sup',
        'close_in_atr', 'close_to_close_sma_4_by_atr',
        'close_to_close_sma_24_by_atr']].copy()
    temp.set_index('entry_datetime', inplace=True)

# for chunk in chunks:
#     predict_by_chunk(data, chunk[0], chunk[1], ticker, amount, RISK_PERC,
#                      direction, conv=conv)
