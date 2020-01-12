# parse:
# system to be read in (ticker, interval, fast, slow, direction)
# look up conversion ticker and read in if applicable (table in calculator
# module).
# merge conversion open value onto signal dataset for entry and exit.

import pandas as pd
from datetime import timedelta
from htp.toolbox import calculator


pd.set_option("display.max_columns", 35)
pd.set_option('max_colwidth', 150)
pd.set_option("display.max_rows", 50)

ticker = 'EUR_USD'
interval = 'H1'
fast = 4
slow = 24
direction = 'sell'

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

if interval == 'H1':
    coeff = 4
elif interval == ' H4':
    coeff = 16
else:
    coeff = 1

# clean up conversion price fields with last known value prior to entry/exit
# timestamp.
for i in ['entry', 'exit']:
    null_conv = data.loc[data[f'conv_{i}_price'].isna()==True, f'{i}_datetime']
    if len(null_conv) > 0:
        for row in null_conv.to_frame().itertuples():
            period = 15 * coeff
            x = False
            while x is False and period <= 1080:
                try:
                    ts = row[1] - timedelta(minutes=period)
                    val = conv.loc[ts, 'open']
                except KeyError:
                    period += (15 * coeff)
                else:
                    data.at[row[0], f'conv_{i}_price'] = val
                    x = True

# backup if not last know value can be found in the preceeding week leading up
# to entry/exit.
data.dropna(subset=['conv_entry_price', 'conv_exit_price'], inplace=True)
