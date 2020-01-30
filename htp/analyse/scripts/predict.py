from htp.aux import tasks
from htp.analyse.scripts.evaluate import parts


def get_data(ticker, granularity, system, multiplier):
    comb = []
    if system[0] != 'close_sma_3 close_sma_5':
        for s in system:
            comb += parts[1 - int(s)]
    else:
        comb = system

    # print(comb)
    for s in comb:
        for trade in ['buy']:  # , 'sell']:
            tasks.setup_predict.delay(
                ticker, granularity, s.split(' ')[0], s.split(' ')[1], trade,
                multiplier)
