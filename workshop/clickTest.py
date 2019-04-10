import click


@click.command()
@click.option('--count', default=1, help='Number of greetings.')
@click.option('--name', prompt='Your name',
              help='The person to greet.')
@click.option('--date', default=None, type=click.DateTime(formats=None))
# @click.argument('filename', type=click.File("r"))
@click.argument('f', type=click.Path(exists=True))
def hello(count, name, date, f):
    """Simple program that greets NAME for a total of COUNT times."""
    for x in range(count):
        if date is not None:
            click.echo('Hello {0}! {1}'.format(name, date))
        else:
            click.echo('Hello {0}!'.format(name))
#    out = filename.read()
#    click.echo(out)
    with open(click.format_filename(f)) as f_:
        outPath = f_.read()
    click.echo(outPath)


if __name__ == '__main__':
    hello()
