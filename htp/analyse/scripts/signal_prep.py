from htp.aux.database import db_session
from htp.analyse.scripts.evaluate import parts
from htp.aux.tasks import prep_signals, conv_price
from htp.toolbox.calculator import ticker_conversion_pairs
from htp.aux.models import getTickerTask, genSignalTask,\
        stochastic, convergence_divergence, ichimoku, relative_strength,\
        momentum

tables = {stochastic: ['percK', 'percD'], ichimoku: ['iky_cat'],
          relative_strength: ['rsi'], momentum: ['adx'],
          convergence_divergence: ['macd', 'signal', 'histogram']}

sup = {'M15': 'H1', 'H1': 'H4'}


def get_data(ticker, granularity, system, multiplier):
    conv = db_session.query(getTickerTask).filter(
        getTickerTask.ticker == ticker_conversion_pairs[ticker],
        getTickerTask.granularity == granularity,
        getTickerTask.price == 'A').first()

    conv_id = conv.id
    if ticker == ticker_conversion_pairs[ticker]:
        conv_id = False

    entry_target = db_session.query(getTickerTask).filter(
        getTickerTask.ticker == ticker, getTickerTask.granularity ==
        granularity, getTickerTask.price == 'M').first()

    entry_sup = db_session.query(getTickerTask).filter(
        getTickerTask.ticker == ticker, getTickerTask.granularity ==
        sup[granularity], getTickerTask.price == 'M').first()

    comb = []
    if system[0] != 'close_sma_3 close_sma_5':
        for s in system:
            comb += parts[1 - int(s)]
    else:
        comb = system

    # print(comb)
    for s in comb:
        for trade in ['buy', 'sell']:
            sig = db_session.query(genSignalTask).filter(
                genSignalTask.batch_id == entry_target.id,
                genSignalTask.fast == s.split(' ')[0],  # 'close_sma_3',
                genSignalTask.slow == s.split(' ')[1],  # 'close_sma_5',
                genSignalTask.trade_direction == trade,
                genSignalTask.exit_strategy == f'trailing_atr_{multiplier}'
                ).first()

            (conv_price.s(
                None, 'entry_datetime', 'conv_entry_price', conv_id, sig.id) |
                conv_price.s(
                    'exit_datetime', 'conv_exit_price', conv_id, sig.id) |
                prep_signals.s(
                    stochastic, tables[stochastic], entry_target.id, sig.id,
                    'target') |
                prep_signals.s(
                    relative_strength, tables[relative_strength],
                    entry_target.id, sig.id, 'target') |
                prep_signals.s(
                    momentum, tables[momentum], entry_target.id, sig.id,
                    'target') |
                prep_signals.s(
                    ichimoku, tables[ichimoku], entry_target.id, sig.id,
                    'target') |
                prep_signals.s(
                    convergence_divergence, tables[convergence_divergence],
                    entry_target.id, sig.id, 'target') |
                prep_signals.s(
                    stochastic, tables[stochastic], entry_sup.id, sig.id,
                    'sup') |
                prep_signals.s(
                    relative_strength, tables[relative_strength], entry_sup.id,
                    sig.id, 'sup') |
                prep_signals.s(
                    momentum, tables[momentum], entry_sup.id, sig.id, 'sup') |
                prep_signals.s(
                    ichimoku, tables[ichimoku], entry_sup.id, sig.id, 'sup') |
                prep_signals.s(
                    convergence_divergence, tables[convergence_divergence],
                    entry_sup.id, sig.id, 'sup')).delay()
