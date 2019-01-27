from functools import partial

import click

echo = partial(click.secho, fg='white')
success = partial(click.secho, fg='green')
warn = partial(click.secho, fg='orange')
error = partial(click.secho, fg='red')
# click.echo(click.style('Hello World!', fg='green'))
