#!/usr/bin/env python
import itertools
import os
import ssl
import warnings
from functools import partial
from pprint import pformat, pprint
from urllib.parse import urlparse

import click
import requests
from click import BadParameter
from click.exceptions import _join_param_hints
from requests import exceptions
from requests.auth import HTTPBasicAuth
from urllib3.exceptions import InsecureRequestWarning, MaxRetryError

warnings.simplefilter("ignore", InsecureRequestWarning)

__version__ = '1.2.1'

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


def printer(level, verbosity, color, msg):
    if verbosity > level:
        click.echo(click.style(str(msg), fg=color))


class ExBadParameter(BadParameter):
    def format_message(self):
        return self.message


class ExParamType(click.ParamType):

    def rfail(self, message, param=None, ctx=None):
        # message = f"Invalid value for {param}"
        raise ExBadParameter(message, ctx=ctx, param=param)


class UrlParamType(ExParamType):
    def convert(self, value, param, ctx):
        try:
            o = urlparse(value)
            assert o.path.endswith('/')
        except AssertionError:
            self.fail(f"Rancher url must ends with '/'")
        except Exception:
            self.fail(f"Invalid url. Should be something like 'https://rancher.example.com:9000/v3/'")

        return value


Url = UrlParamType()


class VerbosityParamType(ExParamType):
    name = 'verbosity'

    def __init__(self) -> None:
        self.quit = False

    def convert(self, value, param, ctx):
        self.total = value
        if param.name == 'quit':
            self.quit = True
        if self.quit:
            value = -1
        return int(value)


Verbosity = VerbosityParamType()


class IChoice(click.Choice):

    def convert(self, value, param, ctx):
        if value in ImagePullPolices:
            value = ImagePullPolices[value]
        return super().convert(value, param, ctx)


class TargetParamType(ExParamType):
    def convert(self, value, param, ctx):
        try:
            parts = value.split(":")
            assert len(parts) == 2
        except Exception:
            self.rfail(f"Invalid value '{value}' for TARGET. Please indicate target in the form 'namespace:workload' ")
        return parts


Target = TargetParamType()


class ProjectParamType(ExParamType):
    def convert(self, value, param, ctx):
        try:
            parts = value.split(":")
            assert len(parts) == 2
        except Exception:
            self.rfail(
                f"Invalid value '{value}' for PROJECT. Please indicate project in the form 'clusterId:projectID' ")
        return parts


Project = ProjectParamType()


class AuthParamType(ExParamType):
    def convert(self, value, param, ctx):
        try:
            parts = value.split(":")
            assert len(parts) == 2
        except Exception:
            self.fail("Please indicate credentials as 'key:secret' ")
        return HTTPBasicAuth(*parts)


Auth = AuthParamType()


class ImageParamType(ExParamType):
    def convert(self, value, param, ctx):
        image = None
        tag = None
        try:
            if '/' in value:
                account, image = value.split("/")
                if ':' in image:
                    image, tag = image.split(':')
                else:
                    tag = 'latest'
            else:
                if ':' in value:
                    raise Exception()
                else:
                    account = value
        except Exception:
            self.fail("Please indicate image in the form 'account[/image[:tag]]' ")
        return account, image, tag


Image = ImageParamType()


def tag_exists(repository, user, image, tag):
    url = f'{repository}/v2/repositories/{user}/{image}/tags/{tag}/'
    response = requests.get(url)
    return response.status_code == 200


def get_available_tags(repository, account, image):
    url = f"{repository}/v2/repositories/{account}/{image}/tags/"
    response = requests.get(url)
    if response.status_code == 200:
        json = response.json()
        return [e['name'] for e in json['results']]
    return None


def get_available_images(repository, account):
    url = f"{repository}/v2/repositories/{account}/"
    response = requests.get(url)
    if response.status_code == 200:
        json = response.json()
        return [e['name'] for e in json['results']]
    return None


ImagePullPolices = {'IfNotPresent': 'IfNotPresent',
                    'Always': 'Always',
                    'Never': 'Never',
                    'ifnotpresent': 'IfNotPresent',
                    'always': 'Always',
                    'never': 'Never',
                    'i': 'IfNotPresent',
                    'a': 'Always',
                    'n': 'Never',
                    }

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

                   ]
_rancher_options = [click.option('-b',
                                 '--base-url',
                                 type=Url,
                                 envvar='RANCHER_ENDPOINT',
                                 help='Rancher base url. [RANCHER_ENDPOINT]'
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
                        type=Target,
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
                                default='https://hub.docker.com',
                                envvar='DOCKER_REPOSITORY',
                                metavar='URL',
                                help='Docker repository [DOCKER_REPOSITORY]'),
                   click.option('--check-image/--no-check-image',
                                is_flag=True,
                                default=True,
                                help='Do not check Docker repository'),
                   ]


def options(*opts):
    def decorator(func):
        for option in itertools.chain(*opts):
            func = option(func)
        return func

    return decorator


a = options(_global_options)
b = options(_rancher_options)
c = options(_workload_options)

class Client:
    def __init__(self, base_url, auth=None, verify=True, debug=False):
        self.auth = auth
        self.verify = verify

    def get(self, url):
        response = requests.get(url, auth=self.auth, verify=self.verify)
        if response.status_code == 404:
            error(f"Workload '{workload}' not found at '{url}'")
            ctx.exit(1)
        elif response.status_code != 200:
            error(f"Error with rancher API at '{url}'")
            error(pformat(response.json()))
            ctx.exit(1)

        return response.json()

def get_target(ctx, repository, base, verbosity, ignore_tag=False):
    error = partial(printer, 0, verbosity, 'red')
    success = partial(printer, 0, verbosity, 'green')

    account, docker_image, docker_tag = base
    if docker_image:
        tags = get_available_tags(repository, account, docker_image)
        if tags:
            if ignore_tag or docker_tag not in tags:
                success(f"Available tags are: {', '.join(tags)}")
                ctx.exit(1)
            else:
                return account, docker_image, docker_tag
        else:
            error("No tags found. Get available images")
            error(f"Image '{docker_image}' not found on {repository}")

    images = get_available_images(repository, account)
    if images:
        success(f"Available images are: {', '.join(images)}")
        ctx.exit(1)
    else:
        error(f"No images found for account '{account}'")

    return account, docker_image, docker_tag


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(__version__)
@options(_global_options)
@click.pass_context
def cli(ctx, *args, **kwargs):
    """ lazo aims to help deployment on new version of Rancher workloads."""
    ctx.obj = kwargs


@cli.command()
@options(_global_options)
@options(_docker_options)
@click.argument('image', type=Image, envvar='DOCKER_IMAGE')
@click.pass_context
def list(ctx, image, verbosity, quit, repository, **kwargs):
    get_target(ctx, repository, image, verbosity, ignore_tag=True)


@cli.command(name='info')
@options(_global_options, _rancher_options)
@options([CLUSTER, PROJECT, WORKLOAD])
@click.pass_context
def _info(ctx, base_url, cluster, project, workload, verbosity, auth, insecure, **kwargs):
    info = partial(printer, 0, verbosity, 'white')

    if not (cluster or project or workload):
        ctx.fail("==========")

    if project:
        cluster_id, project_id = project
        project_url = f'{base_url}projects/{cluster_id}:{project_id}/projects'
        response = requests.get(project_url, auth=auth, verify=not insecure).json()
        for project in response['data']:
            info(f"\t{project['name']} {project['id']}")

    elif cluster:
        url = f'{base_url}clusters'
        response = requests.get(url, auth=auth, verify=not insecure).json()
        for cluster in response['data']:
            info(f"{cluster['name']} {cluster['id']}")
            # projects = https://r.singlewave.co.uk:10443/v3/clusters/c-wwk6v/projects
            project_url = f'{base_url}clusters/{cluster["id"]}/projects'
            response = requests.get(project_url, auth=auth, verify=not insecure).json()
            for project in response['data']:
                info(f"\t{project['name']} {project['id']}")

        # pprint(json)


# namespace, workload = target
# info = partial(printer, 2, verbosity, 'white')
#
# url = f'{base_url}project/{cluster}:{project}/workloads/deployment:{namespace}:{workload}'
# info(f"Fetching informations at '{url}'")
# response = requests.get(url, auth=auth, verify=not insecure)
#
# json = response.json()
# for pod in json['containers']:
#     info(pod)


#
# @cli.command()
# @options(_global_options)
# @click.argument('workload')
# @click.pass_context
# def shell(ctx, base_url, cluster, project, **kwargs):
#     url = f'{base_url}project/{cluster}:{project}/workloads/deployment:{namespace}:{workload}'
#     requests.post(url)
#
# # curl -u “${CATTLE_ACCESS_KEY}:${CATTLE_SECRET_KEY}” -X POST
# #     -H ‘Accept: application/json’
# #     -H ‘Content-Type: application/json’
# #     -d ‘{“attachStdin”:false, “attachStdout”:false, “command”:[“service”, “apache-perl”, “stop”], “tty”:false}’
# #     “$RANCHER_URL/v1/projects/1a5/containers/1i156/?action=execute”
#

@cli.command()
@options(_global_options)
@options(_rancher_options)
@options(_docker_options)
@click.argument('target', type=Target, envvar='RANCHER_TARGET')
@click.argument('image', type=Image, envvar='DOCKER_IMAGE')
@click.pass_context
def upgrade(ctx, target, image, auth,
            base_url, cluster, project,
            pull_policy,
            stdin,
            name,
            verbosity, quit, insecure, repository, check_image, dry_run):
    error = partial(printer, 0, verbosity, 'red')
    log = partial(printer, 1, verbosity, 'white')
    info = partial(printer, 2, verbosity, 'white')
    success = partial(printer, 0, verbosity, 'green')

    account, docker_image, docker_tag = image

    image_full_name = f"{account}/{docker_image}:{docker_tag}"
    if check_image:
        get_target(ctx, repository, image, verbosity)

    if stdin or ctx.obj.get('stdin'):
        credentials = click.get_text_stream('stdin').read()
        try:
            key, secret = credentials[:-1].split(":")
        except ValueError:
            ctx.fail("Invalid credential using stdin. Use format 'key:secret'")

    namespace, workload = target
    url = f'{base_url}project/{cluster}:{project}/workloads/deployment:{namespace}:{workload}'

    try:
        try:
            info(f"Fetching informations at '{url}'")
            response = requests.get(url, auth=auth, verify=not insecure)
        except (InsecureRequestWarning, ssl.SSLError, MaxRetryError, exceptions.SSLError):
            error("SSL certificate validation failed. Try to use '--insecure', "
                  "if you know what you are doing.")
            ctx.exit(1)

        if response.status_code == 404:
            error(f"Workload '{workload}' not found at '{url}'")
            ctx.exit(1)
        elif response.status_code != 200:
            error(f"Error with rancher API at '{url}'")
            error(pformat(response.json()))
            ctx.exit(1)

        json = response.json()
        found = set()
        try:
            for pod in json['containers']:
                found.add(pod['image'])
                pod['image'] = image_full_name
                pod['imagePullPolicy'] = pull_policy
                if name:
                    pod['name'] = name
            info(f"Found {len(json['containers'])} pod(s)")
            info(f"Existing tags are: {','.join(found)}")
        except Exception:
            error("ERROR: Unexpectd response")
            error(pformat(json))
            ctx.exit(1)

        log(f"Updating all pod(s) to {image_full_name}")
        if not dry_run:
            response = requests.put(url, json=json, auth=auth, verify=not insecure)
            if response.status_code == 200:
                success("Success")
                ctx.exit(0)
            else:
                error(f"Error with rancher API at '{url}'")
                error(pformat(response.json()))
                ctx.exit(1)
        else:
            success(f"'--dry-run' used. Exiting without real update")

    except exceptions.InvalidSchema:
        error(f"Invalid rancher url '{base_url}'")
        ctx.exit(1)
    except exceptions.ConnectionError:
        error("Unable to connect ", color=True)
        ctx.exit(1)


if __name__ == '__main__':
    cli()
