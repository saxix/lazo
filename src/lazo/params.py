import inspect
import itertools

import click
from click import Option
from click.decorators import _param_memo

from .types import Auth, DebugMode, IChoice, Project, StdinAuth, Url, Verbosity


class OOption(Option):
    pass
    # def __init__(self, param_decls=None, show_default=True, prompt=False, confirmation_prompt=False, hide_input=False,
    #              is_flag=None, flag_value=None, multiple=False, count=False, allow_from_autoenv=True, type=None,
    #              help=None, hidden=False, show_choices=True, show_envvar=True, **attrs):
    #     super().__init__(param_decls, show_default, prompt, confirmation_prompt, hide_input, is_flag, flag_value,
    #                      multiple, count, allow_from_autoenv, type, help, hidden, show_choices, show_envvar, **attrs)


all_envs = {}


def make_option(*param_decls, **attrs):
    global all_envs
    if "envvar" in attrs:
        e = attrs["envvar"]
        all_envs[e] = None

    # print("src/lazo/params.py: 25", 11111, attrs.get('envvar'))
    def decorator(f):
        # Issue 926, copy attrs, so pre-defined options can re-use the same cls=
        option_attrs = attrs.copy()

        if "help" in option_attrs:
            option_attrs["help"] = inspect.cleandoc(option_attrs["help"])
        OptionClass = option_attrs.pop("cls", Option)
        opt = OptionClass(param_decls, **option_attrs)
        _param_memo(f, opt)
        if "envvar" in attrs:
            e = attrs["envvar"]
            all_envs[e] = opt
        return f

    return decorator


_global_options = [
    make_option(
        "-v",
        "--verbosity",
        default=1,
        type=Verbosity,
        help="verbosity level",
        count=True,
    ),
    make_option(
        "-q", "--quiet", help="no output", default=0, is_flag=True, type=Verbosity
    ),
    make_option("-d", "--dry-run", is_flag=True, help="dry-run mode"),
    make_option(
        "--debug",
        default=False,
        is_flag=True,
        flag_value=True,
        type=DebugMode,
        help="debug mode",
    ),
]

_rancher_options = [
    make_option(
        "-b",
        "--base-url",
        required=False,
        type=Url,
        envvar="RANCHER_BASE_URL",
        cls=OOption,
        help="Rancher base url.",
        metavar="URL",
    ),
    make_option(
        "--auth",
        envvar="RANCHER_AUTH",
        help="Rancher API key:secret",
        type=Auth,
        cls=OOption,
        default=None,
        metavar="TEXT",
    ),
    make_option("--stdin", is_flag=True, help="Read credentials from stdin"),
    make_option(
        "-i",
        "--insecure",
        is_flag=True,
        envvar="RANCHER_INSECURE",
        cls=OOption,
        help="Ignore verifying the SSL certificate",
    ),
    make_option(
        "-n",
        "--use-names",
        envvar="RANCHER_USE_NAMES",
        is_flag=True,
        help="Use target names instead of Rancher Id(s)",
    ),
]
CLUSTER = make_option(
    "-c",
    "--cluster",
    required=True,
    envvar="RANCHER_CLUSTER",
    help="Rancher cluster key.",
    cls=OOption,
    metavar="TEXT",
)
PROJECT = make_option(
    "-p",
    "--project",
    required=True,
    type=Project,
    envvar="RANCHER_PROJECT",
    cls=OOption,
    help="Rancher project key",
    metavar="PROJECT",
)
# WORKLOAD = make_option('-w',
#                        '--workload',
#                        type=Workload,
#                        envvar='RANCHER_WORKLOAD',
#                        cls=OOption,
#                        help='Rancher workload.',
#                        metavar='TEXT')

_workload_options = [
    CLUSTER,
    PROJECT,
    make_option(
        "--pull",
        "pull_policy",
        type=IChoice(["IfNotPresent", "Always", "Never"]),
        default="Always",
        help="Rancher ImagePullPolicy",
    ),
    make_option("--name", help="Workload new name"),
]
#
# _docker_options = [make_option('-r',
#                                '--repository',
#                                default='https://hub.docker.com/v2',
#                                envvar='DOCKER_REPOSITORY',
#                                metavar='URL',
#                                cls=OOption,
#                                help='Docker repository'),
#                    make_option('-u', '--username',
#                                help='username'),
#                    make_option('-p', '--password',
#                                help='password'),
#                    make_option('--check-image/--no-check-image',
#                                is_flag=True,
#                                default=True,
#                                help='Do not check Docker repository'),
#                    make_option('--stdin',
#                                type=StdinAuth,
#                                is_flag=True,
#                                help='Read credentials from stdin'),
#                    ]


def options(*opts):
    def decorator(func):
        for option in reversed(list(itertools.chain(*opts))):
            func = option(func)
        return func

    return decorator

#
# class Config(object):
#     def __init__(self, root):
#         self.root = root
#         self.client = None
#         self.storage = {}
#
#     def __repr__(self):
#         return "<Config>"
#
#
# pass_config = click.make_pass_decorator(Config)
