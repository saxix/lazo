#!/usr/bin/env python
import os
import sys
import warnings

import click
from urllib3.exceptions import InsecureRequestWarning

import lazo

from .params import _global_options, all_envs, make_option, options
from .utils import import_by_name

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
warnings.simplefilter("ignore", InsecureRequestWarning)


class MyCLI(click.Group):

    def __init__(self, name=None, commands=None, **attrs):
        self.debug = False
        super().__init__(name, commands, **attrs)


def display(value):
    if value is None:
        return ''
    return str(value)


PROTECTED = ['auth']


@click.group(context_settings=CONTEXT_SETTINGS, cls=MyCLI, invoke_without_command=True, no_args_is_help=True)
@click.version_option(lazo.__version__)
@make_option('--env', is_flag=True, is_eager=True)
@make_option('--defaults', is_flag=True, is_eager=True)
@options(_global_options)
@click.pass_context
def cli(ctx, env, defaults, **kwargs):
    def get_value(opt):
        v = os.environ.get(opt.envvar, opt.default)
        if opt.is_flag:
            value = opt.type.convert(v, opt.name, click.get_current_context())
        else:
            value = os.environ.get(opt.envvar, opt.default) or ''
        if opt.name in PROTECTED:
            value = '***' if value else ''
        return str(value), 'from env' if opt.envvar in os.environ else ''

    if defaults:
        click.echo(f"{'Env':<20} {'Value':<50} Origin")
        for i, opt in sorted(all_envs.items()):
            name = opt.name
            value, descr = get_value(opt)
            click.echo(f"{name:<20} {value:<50} {descr}")
        sys.exit(0)
    elif env:
        click.echo(f"{'Env':<20} Value")
        for i, opt in sorted(all_envs.items()):
            value, in_env = get_value(opt)
            if in_env:
                click.echo(f"{i:<20} {value:<30}")
            else:
                click.echo(f"{i:<20} -- not set --")
        sys.exit(0)
    ctx.obj = {}


cli.add_command(import_by_name('lazo.commands.rancher.rancher'))
cli.add_command(import_by_name('lazo.commands.docker.docker'))

if __name__ == '__main__':
    cli()
