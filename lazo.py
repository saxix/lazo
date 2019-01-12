#!/usr/bin/env python
import ssl
import sys
import warnings
from pprint import pprint

import click
import requests
from requests.auth import HTTPBasicAuth
from requests import exceptions
from urllib3.exceptions import InsecureRequestWarning, MaxRetryError

warnings.simplefilter("ignore", InsecureRequestWarning)

class VerbosityParamType(click.ParamType):
    name = 'verbosity'

    def __init__(self) -> None:
        self.quit = False

    def convert(self, value, param, ctx):
        self.total = value
        if param.name == 'quit':
            self.quit = True
        if self.quit:
            value = 0
        return int(value)


Verbosity = VerbosityParamType()

_global_options = [
    click.option('-v', '--verbosity',
                 default=1,
                 type=Verbosity,
                 count=True),
    click.option('-q', '--quit',
                 default=0, is_flag=True, type=Verbosity),
    click.option('-u',
                 '--username',
                 envvar='RANCHER_USERNAME',
                 help='RANCHER_USERNAME',
                 metavar='USERNAME'),
    click.option('-p',
                 '--password',
                 envvar='RANCHER_PASSWORD',
                 help='RANCHER_PASSWORD',
                 metavar='PASSWORD'),
    click.option('-b',
                 '--base-url',
                 envvar='RANCHER_ENDPOINT',
                 help='RANCHER_ENDPOINT',
                 metavar='ENDPOINT'),
    click.option('-w',
                 '--workload',
                 envvar='RANCHER_WORKLOAD',
                 help='RANCHER_WORKLOAD',
                 metavar='WORKLOAD'),
    click.option('-c',
                 '--cluster',
                 envvar='RANCHER_CLUSTER',
                 help='RANCHER_CLUSTER',
                 metavar='CLUSTER'),
    click.option('-i',
                 '--insecure',
                 is_flag=True,
                 envvar='RANCHER_INSECURE',
                 help='RANCHER_INSECURE'),
]


def global_options(func):
    for option in reversed(_global_options):
        func = option(func)
    return func


@click.group()
@global_options
@click.pass_context
def cli(ctx, *args, **kwargs):
    pass


@cli.command()
@global_options
@click.argument('image')
@click.pass_context
def upgrade(ctx, image, username, password, base_url, verbosity, workload, cluster, quit, insecure):
    auth = HTTPBasicAuth(username, password)
    url = f'{base_url}/project/c-wwk6v:p-xd4dg/workloads/deployment:{cluster}:{workload}'
    try:
        if verbosity>1:
            click.echo(url)
        response = requests.get(url, auth=auth, verify=not insecure)
    except (InsecureRequestWarning, ssl.SSLError, MaxRetryError, exceptions.SSLError):
        click.echo("SSL certificate validation failed. Try to use '--insecure', if you know what you are doing.",
                   color=True)
        sys.exit(1)
    json = response.json()
    for c in json['containers']:
        c['image'] = image
    response = requests.put(url, json=json, auth=auth, verify=not insecure)
    if response.status_code != 200:
        pprint(response.json())


if __name__ == '__main__':
    cli()
