#!/usr/bin/env python
import ssl
import warnings
from functools import partial
from pprint import pformat
from urllib.parse import urlparse

import click
import requests
from requests import exceptions
from requests.auth import HTTPBasicAuth
from urllib3.exceptions import InsecureRequestWarning, MaxRetryError

warnings.simplefilter("ignore", InsecureRequestWarning)

__version__ = '1.2.1'

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


def printer(level, verbosity, color, msg):
    if verbosity > level:
        click.echo(click.style(str(msg), fg=color))


class UrlParamType(click.ParamType):
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


class VerbosityParamType(click.ParamType):
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


class TargetParamType(click.ParamType):
    def convert(self, value, param, ctx):
        try:
            parts = value.split(":")
            assert len(parts) == 2
        except Exception:
            self.fail("Please indicate target in the form 'namespace:workload' ")
        return parts


Target = TargetParamType()


class ImageParamType(click.ParamType):
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

_global_options = [
    click.option('-v', '--verbosity',
                 default=1,
                 type=Verbosity,
                 help="verbosity level",
                 count=True),
    click.option('-q', '--quit',
                 help="no output",
                 default=0, is_flag=True, type=Verbosity),
    click.option('-k',
                 '--key',
                 envvar='RANCHER_KEY',
                 help='Rancher API Key (username) [RANCHER_KEY]',
                 metavar='KEY'),
    click.option('-s',
                 '--secret',
                 envvar='RANCHER_SECRET',
                 help='Rancher API secret (password) [RANCHER_SECRET]',
                 metavar='SECRET'),
    click.option('--stdin',
                 is_flag=True,
                 help='Read credentials from stdin'),
    click.option('-r',
                 '--repository',
                 default='https://hub.docker.com',
                 envvar='DOCKER_REPOSITORY',
                 metavar='URL',
                 help='Docker repository [DOCKER_REPOSITORY]'),
    click.option('--check-image/--no-check-image',
                 is_flag=True,
                 default=True,
                 help='Do not check Docker repository'),
    click.option('-b',
                 '--base-url',
                 type=Url,
                 envvar='RANCHER_ENDPOINT',
                 help='Rancher base url',
                 metavar='URL'),
    click.option('-c',
                 '--cluster',
                 envvar='RANCHER_CLUSTER',
                 help='Rancher cluster key [RANCHER_CLUSTER]',
                 metavar='TEXT'),
    click.option('-p',
                 '--project',
                 required=True,
                 envvar='RANCHER_PROJECT',
                 help='Rancher project key [RANCHER_PROJECT]',
                 metavar='TEXT'),
    click.option('-i',
                 '--insecure',
                 is_flag=True,
                 envvar='RANCHER_INSECURE',
                 help='Ignore verifying the SSL certificate [RANCHER_INSECURE]'),
    click.option('-d',
                 '--dry-run',
                 is_flag=True,
                 help='dry-run mode'),
    click.option('--pull', 'pull_policy',
                 type=IChoice(['IfNotPresent', 'Always', 'Never'], False),
                 default='Always',
                 help='Rancher ImagePullPolicy'),
    click.option('--name',
                 help='Workload new name'),
]


def global_options(func):
    for option in reversed(_global_options):
        func = option(func)
    return func


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
@global_options
@click.pass_context
def cli(ctx, *args, **kwargs):
    """ lazo aims to help deployment on new version of Rancher workloads."""
    ctx.obj = kwargs


@cli.command()
@global_options
@click.argument('image', type=Image, envvar='DOCKER_IMAGE')
@click.pass_context
def list(ctx, image, verbosity, quit, repository, **kwargs):
    get_target(ctx, repository, image, verbosity, ignore_tag=True)



@cli.command()
@global_options
@click.argument('target', type=Target, envvar='RANCHER_TARGET')
@click.argument('image', type=Image, envvar='DOCKER_IMAGE')
@click.pass_context
def upgrade(ctx, target, image, key, secret,
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

    auth = HTTPBasicAuth(key, secret)

    namespace, workload = target
    url = f'{base_url}project/{cluster}:{project}/workloads/deployment:{namespace}:{workload}'
    info(f"Authenticating as '{key}'")

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
