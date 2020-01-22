# parse:
# system to be read in (ticker, interval, fast, slow, direction)
# look up conversion ticker and read in if applicable (table in calculator
# module).
# merge conversion open value onto signal dataset for entry and exit.

import pandas as pd
from datetime import timedelta
from htp.toolbox import calculator
from htp.analyse.machine_learn import predict

pd.set_option("display.max_columns", 35)
pd.set_option('max_colwidth', 150)
pd.set_option("display.max_rows", 50)

amount = 1000
RISK_PERC = 0.01
ticker = 'EUR_USD'
conv = True
interval = 'H1'
fast = 4
slow = 24
direction = 'sell'
train_sample_size = 500
test_sample_size = 50


with pd.HDFStore(
  f'data/{ticker}/{interval}/signals/{direction}-close_sma_{fast}-close_sma_{slow}.h5') as store:
    data = store['S']

conv_ticker = calculator.ticker_conversion_pairs[ticker]
with pd.HDFStore(f'data/{conv_ticker}/{interval}/price.h5') as store:
    conv = store['A']

data = data.merge(conv['open'], how='left', left_on='entry_datetime',
                  right_index=True, validate='1:1')
data.rename(columns={'open': 'conv_entry_price'}, inplace=True)
data = data.merge(conv['open'], how='left', left_on='exit_datetime',
                  right_index=True, validate='1:1')
data.rename(columns={'open': 'conv_exit_price'}, inplace=True)

coeff = {'M15': 1, 'H1': 4, 'H4': 16}

# clean up conversion price fields with last known value prior to entry/exit
# timestamp.
for i in ['entry', 'exit']:
    null_conv = data.loc[data[f'conv_{i}_price'].isna()==True, f'{i}_datetime']
    if len(null_conv) > 0:
        for row in null_conv.to_frame().itertuples():
            x = False
            period = 15 * coeff[interval]
            # period increases in 15 minute multiplied by required coefficient
            # to equal 1 corresponding time interval.
            while x is False and period <= 10080:
                try:
                    ts = row[1] - timedelta(minutes=period)
                    val = conv.loc[ts, 'open']
                except KeyError:
                    period += (15 * coeff[interval])
                else:
                    data.at[row[0], f'conv_{i}_price'] = val
                    x = True

# backup if no last know value can be found in the preceeding week leading up
# to entry/exit.
data.dropna(subset=['conv_entry_price', 'conv_exit_price'], inplace=True)

num_chunks = ((len(results) - train_sample_size - test_sample_size) /
              test_sample_size) + 2

chunks = []
for ind in range(int(num_chunks)):
    # chunks.append((ind * 100, ind * 100 + 499))
    chunks.append(
        (ind * test_sample_size, ind * test_sample_size +
         train_sample_size + test_sample_size))


def predict_by_chunk(data, start, end, ticker, amount, RISK_PERC, trade_type,
                     conv=False):
    sub_data = data.iloc[start:end].copy()
    results = calculator.count(
        sub_data, ticker, amount, RISK_PERC, direction, conv=conv)
    performance = calculator.performance_stats(results)
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

for chunk in chunks:
    predict_by_chunk(data, chunk[0], chunk[1], ticker, amount, RISK_PERC,
                     direction, conv=conv)
