from htp.analyse import indicator, observe
from bokeh.layouts import column
from bokeh.plotting import figure
from bokeh.io import show, output_file
from bokeh.models import LinearAxis, Range1d


def candlestick_chart(df, overlay, indicator, ind_overlay, title):
    df.reset_index(inplace=True)
    inc = df.close > df.open
    dec = df.open > df.close
    p = figure(plot_width=1000, plot_height=600, title=title)
    p.xaxis.major_label_overrides = {
        i: date.strftime('%b %d %H:%M:%S') for i, date in enumerate(
            df['index'])}
    p.xaxis.bounds = (0, df.index[-1])
    p.segment(df.index, df.high, df.index, df.low, color='black')
    p.vbar(
        df.index[inc], 0.5, df.open[inc], df.close[inc], fill_color='#D5E1DD',
        line_color='black')
    p.vbar(
        df.index[dec], 0.5, df.open[dec], df.close[dec], fill_color='#F2583E',
        line_color='black')
    p.line(df.index, overlay, line_width=2)

    ind = figure(plot_width=1000, plot_height=200, y_range=(0, 100))
    ind.xaxis.major_label_overrides = {
        i: date.strftime('%b %d %H:%M:%S') for i, date in enumerate(
            df['index'])}
    ind.xaxis.bounds = (0, df.index[-1])
    ind.ygrid.ticker = [30., 50., 70.]
    ind.line(df.index, indicator, line_width=1)
    ind.extra_y_ranges = {'signal': Range1d(start=-1.1, end=1.1)}
    ind.line(df.index, ind_overlay, color='black', y_range_name='signal')
    ind.add_layout(LinearAxis(y_range_name='signal'), 'right')

    output_file('basic.html')
    show(column(p, ind))


def test_candlestick_chart(data):
    df = data[100:300]
    ind = indicator.Indicate(data)
    sma = ind.smooth_moving_average(14)['close_sma_14'][100:300]
    rsi = ind.relative_strength_index()
    rsi_overlay = observe.trend_relative_strength_index(rsi)[100:300]
    candlestick_chart(df, sma, rsi['rsi'][100:300], rsi_overlay, 'AUD_JPY')
