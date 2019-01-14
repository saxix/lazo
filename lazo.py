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
        try:
            account, image = value.split("/")
            if ':' in image:
                image, tag = image.split(':')
            else:
                tag = 'latest'
        except Exception:
            self.fail("Please indicate image in the form 'account/image' ")
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
                 help='Rancher API Key (username)',
                 metavar='KEY'),
    click.option('-s',
                 '--secret',
                 envvar='RANCHER_SECRET',
                 help='Rancher API secret (password)',
                 metavar='SECRET'),
    click.option('--stdin',
                 is_flag=True,
                 help='Read credentials from stdin'),
    click.option('-r',
                 '--repository',
                 default='https://hub.docker.com',
                 envvar='DOCKER_REPOSITORY',
                 metavar='URL',
                 help='Docker repository'),
    click.option('--check-image/--no-check-image',
                 is_flag=True,
                 default=True,
                 help='Do not check Docker repository'),
    click.option('-b',
                 '--base-url',
                 type=Url(),
                 envvar='RANCHER_ENDPOINT',
                 help='Rancher base url',
                 metavar='URL'),
    click.option('-c',
                 '--cluster',
                 envvar='RANCHER_CLUSTER',
                 help='Rancher cluster key',
                 metavar='TEXT'),
    click.option('-p',
                 '--project',
                 required=True,
                 envvar='RANCHER_PROJECT',
                 help='Rancher project key',
                 metavar='TEXT'),
    click.option('-i',
                 '--insecure',
                 is_flag=True,
                 envvar='RANCHER_INSECURE',
                 help='Ignore verifying the SSL certificate '),
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


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(__version__)
@global_options
@click.pass_context
def cli(ctx, *args, **kwargs):
    """ lazo aims to help deployment on new version of Rancher workloads."""
    ctx.obj = kwargs


@cli.command()
@global_options
@click.argument('target', type=Target, envvar='HOME')
@click.argument('image', type=Image)
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
        log("Checking image on docker hub")
        if not tag_exists(repository, account, docker_image, docker_tag):
            tags = get_available_tags(repository, account, docker_image)
            if tags:
                error(f"Tag '{docker_tag}' not found on {repository}")
                error(f"Available tags are: {', '.join(tags)}")
                ctx.exit(1)
            else:
                log("No tags found. Get available images")
                images = get_available_images(repository, account)
                if images:
                    error(f"Image '{docker_image}' not found on {repository}")
                    error(f"Available images are: {', '.join(images)}")
                    ctx.exit(1)
                else:
                    error(f"No images found for account '{account}'")

            error(f"Cannot retrieve image {image_full_name}")
            ctx.exit()
        else:
            info(f"Image found on {repository}")

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
            info(f"'--dry-run' used. Exiting without real update")

    except exceptions.InvalidSchema:
        error(f"Invalid rancher url '{base_url}'")
        ctx.exit(1)
    except exceptions.ConnectionError:
        error("Unable to connect ", color=True)
        ctx.exit(1)


if __name__ == '__main__':
    cli()
