import itertools
import os

import click

from lazo.types import (Auth, DebugMode, IChoice, Project,
                        StdinAuth, Url, Verbosity, Workload,)

_global_options = [click.option('-v', '--verbosity',
                                default=1,
                                type=Verbosity,
                                help="verbosity level",
                                count=True),
                   click.option('-q', '--quit',
                                help="no output",
                                default=0, is_flag=True, type=Verbosity),
                   click.option('-d',
                                '--dry-run',
                                is_flag=True,
                                help='dry-run mode'),
                   click.option('--debug',
                                is_flag=True,
                                type=DebugMode,
                                help='debug mode'),
                   ]

_rancher_options = [click.option('-b',
                                 '--base-url',
                                 required=True,
                                 type=Url,
                                 envvar='RANCHER_ENDPOINT',
                                 help='Rancher base url. [RANCHER_ENDPOINT]\n'
                                      'Default: %s' % os.environ.get('RANCHER_ENDPOINT'),
                                 metavar='URL'),

                    click.option('--auth',
                                 envvar='RANCHER_AUTH',
                                 help='Rancher API key:secret [RANCHER_AUTH]',
                                 type=Auth,
                                 default=None,
                                 metavar='TEXT'),
                    click.option('--stdin',
                                 is_flag=True,
                                 help='Read credentials from stdin'),
                    click.option('-i',
                                 '--insecure',
                                 is_flag=True,
                                 envvar='RANCHER_INSECURE',
                                 help='Ignore verifying the SSL certificate [RANCHER_INSECURE]'),
                    click.option('-n',
                                 '--use-names',
                                 is_flag=True,
                                 help='Use target names instead of internal Id(s)'),
                    ]
CLUSTER = click.option('-c',
                       '--cluster',
                       envvar='RANCHER_CLUSTER',
                       help='Rancher cluster key. [RANCHER_CLUSTER]. '
                            'Default: %s' % os.environ.get('RANCHER_CLUSTER'),
                       metavar='TEXT')
PROJECT = click.option('-p',
                       '--project',
                       type=Project,
                       envvar='RANCHER_PROJECT',
                       help='Rancher project key [RANCHER_PROJECT].'
                            'Default: %s' % os.environ.get('RANCHER_PROJECT'),
                       metavar='PROJECT')
WORKLOAD = click.option('-w',
                        '--workload',
                        type=Workload,
                        envvar='RANCHER_WORKLOAD',
                        help='Rancher workload [RANCHER_WORKLOAD].'
                             'Default: %s' % os.environ.get('RANCHER_WORKLOAD'),
                        metavar='TEXT')

_workload_options = [CLUSTER,
                     PROJECT,
                     click.option('--pull', 'pull_policy',
                                  type=IChoice(['IfNotPresent', 'Always', 'Never'], False),
                                  default='Always',
                                  help='Rancher ImagePullPolicy'),
                     click.option('--name',
                                  help='Workload new name'),
                     ]

_docker_options = [click.option('-r',
                                '--repository',
                                default='https://hub.docker.com/v2',
                                envvar='DOCKER_REPOSITORY',
                                metavar='URL',
                                help='Docker repository [DOCKER_REPOSITORY]'),
                   click.option('-u', '--username',
                                help='username'),
                   click.option('-p', '--password',
                                help='password'),
                   click.option('--check-image/--no-check-image',
                                is_flag=True,
                                default=True,
                                help='Do not check Docker repository'),
                   click.option('--stdin',
                                type=StdinAuth,
                                is_flag=True,
                                help='Read credentials from stdin'),
                   ]


def options(*opts):
    def decorator(func):
        for option in reversed(list(itertools.chain(*opts))):
            func = option(func)
        return func

    return decorator


class Config(object):

    def __init__(self, root):
        self.root = root
        self.client = None
        self.storage = {}

    def __repr__(self):
        return '<Config>'


pass_config = click.make_pass_decorator(Config)
