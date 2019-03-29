import click
from api import oanda


@click.command()
def cli():
    """Example script."""
    click.echo('Hello World!')

    ticker = "EUR_USD"
    arguments = {"count": "6", "price": "M", "granularity": "S5"}
    r = oanda.Instrument("api/config.ini")
    data = r.candles(ticker, arguments)
    click.echo(data.json())


if __name__ == '__main__':
    cli()
