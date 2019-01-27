#!/usr/bin/env python
import warnings

import click
from urllib3.exceptions import InsecureRequestWarning

import lazo
from lazo.params import _global_options, options

from .utils import import_by_name

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
warnings.simplefilter("ignore", InsecureRequestWarning)


class MyCLI(click.Group):

    def __init__(self, name=None, commands=None, **attrs):
        self.debug = False
        super().__init__(name, commands, **attrs)


@click.group(context_settings=CONTEXT_SETTINGS, cls=MyCLI)
@click.version_option(lazo.__version__)
@options(_global_options)
@click.pass_context
def cli(ctx, **kwargs):
    ctx.obj = {}


cli.add_command(import_by_name('lazo.commands.rancher.rancher'))
cli.add_command(import_by_name('lazo.commands.docker.docker'))

#
# @cli.command()
# @options(_global_options)
# @options(_docker_options)
# @click.argument('image', type=Image, envvar='DOCKER_IMAGE')
# @click.pass_context
# def list(ctx, image, verbosity, quit, repository, **kwargs):
#     get_target(ctx, repository, image, verbosity, ignore_tag=True)
#
#
# @cli.command(name='info')
# @options(_global_options, _rancher_options)
# @options([CLUSTER, PROJECT, WORKLOAD])
# @click.pass_context
# def _info(ctx, base_url, cluster, project, workload, verbosity, auth, insecure, **kwargs):
#     info = partial(printer, 0, verbosity, 'white')
#
#     if not (cluster or project or workload):
#         ctx.fail("==========")
#
#     if project:
#         cluster_id, project_id = project
#         project_url = f'{base_url}projects/{cluster_id}:{project_id}/projects'
#         response = requests.get(project_url, auth=auth, verify=not insecure).json()
#         for project in response['data']:
#             info(f"\t{project['name']} {project['id']}")
#
#     elif cluster:
#         url = f'{base_url}clusters'
#         response = requests.get(url, auth=auth, verify=not insecure).json()
#         for cluster in response['data']:
#             info(f"{cluster['name']} {cluster['id']}")
#             # projects = https://r.singlewave.co.uk:10443/v3/clusters/c-wwk6v/projects
#             project_url = f'{base_url}clusters/{cluster["id"]}/projects'
#             response = requests.get(project_url, auth=auth, verify=not insecure).json()
#             for project in response['data']:
#                 info(f"\t{project['name']} {project['id']}")
#
#         # pprint(json)
#
#
# # namespace, workload = target
# # info = partial(printer, 2, verbosity, 'white')
# #
# # url = f'{base_url}project/{cluster}:{project}/workloads/deployment:{namespace}:{workload}'
# # info(f"Fetching informations at '{url}'")
# # response = requests.get(url, auth=auth, verify=not insecure)
# #
# # json = response.json()
# # for pod in json['containers']:
# #     info(pod)
#
#
# #
# # @cli.command()
# # @options(_global_options)
# # @click.argument('workload')
# # @click.pass_context
# # def shell(ctx, base_url, cluster, project, **kwargs):
# #     url = f'{base_url}project/{cluster}:{project}/workloads/deployment:{namespace}:{workload}'
# #     requests.post(url)
# #
# # # curl -u “${CATTLE_ACCESS_KEY}:${CATTLE_SECRET_KEY}” -X POST
# # #     -H ‘Accept: application/json’
# # #     -H ‘Content-Type: application/json’
# # #     -d ‘{“attachStdin”:false, “attachStdout”:false, “command”:[“service”, “apache-perl”, “stop”], “tty”:false}’
# # #     “$RANCHER_URL/v1/projects/1a5/containers/1i156/?action=execute”
# #
#
# @cli.command()
# @options(_global_options)
# @options(_rancher_options)
# @options(_docker_options)
# @click.argument('target', type=Target, envvar='RANCHER_TARGET')
# @click.argument('image', type=Image, envvar='DOCKER_IMAGE')
# @click.pass_context
# def upgrade(ctx, target, image, auth,
#             base_url, cluster, project,
#             pull_policy,
#             stdin,
#             name,
#             verbosity, quit, insecure, repository, check_image, dry_run):
#     error = partial(printer, 0, verbosity, 'red')
#     log = partial(printer, 1, verbosity, 'white')
#     info = partial(printer, 2, verbosity, 'white')
#     success = partial(printer, 0, verbosity, 'green')
#
#     account, docker_image, docker_tag = image
#
#     image_full_name = f"{account}/{docker_image}:{docker_tag}"
#     if check_image:
#         get_target(ctx, repository, image, verbosity)
#
#     if stdin or ctx.obj.get('stdin'):
#         credentials = click.get_text_stream('stdin').read()
#         try:
#             key, secret = credentials[:-1].split(":")
#         except ValueError:
#             ctx.fail("Invalid credential using stdin. Use format 'key:secret'")
#
#     namespace, workload = target
#     url = f'{base_url}project/{cluster}:{project}/workloads/deployment:{namespace}:{workload}'
#
#     try:
#         try:
#             info(f"Fetching informations at '{url}'")
#             response = requests.get(url, auth=auth, verify=not insecure)
#         except (InsecureRequestWarning, ssl.SSLError, MaxRetryError, exceptions.SSLError):
#             error("SSL certificate validation failed. Try to use '--insecure', "
#                   "if you know what you are doing.")
#             ctx.exit(1)
#
#         if response.status_code == 404:
#             error(f"Workload '{workload}' not found at '{url}'")
#             ctx.exit(1)
#         elif response.status_code != 200:
#             error(f"Error with rancher API at '{url}'")
#             error(pformat(response.json()))
#             ctx.exit(1)
#
#         json = response.json()
#         found = set()
#         try:
#             for pod in json['containers']:
#                 found.add(pod['image'])
#                 pod['image'] = image_full_name
#                 pod['imagePullPolicy'] = pull_policy
#                 if name:
#                     pod['name'] = name
#             info(f"Found {len(json['containers'])} pod(s)")
#             info(f"Existing tags are: {','.join(found)}")
#         except Exception:
#             error("ERROR: Unexpectd response")
#             error(pformat(json))
#             ctx.exit(1)
#
#         log(f"Updating all pod(s) to {image_full_name}")
#         if not dry_run:
#             response = requests.put(url, json=json, auth=auth, verify=not insecure)
#             if response.status_code == 200:
#                 success("Success")
#                 ctx.exit(0)
#             else:
#                 error(f"Error with rancher API at '{url}'")
#                 error(pformat(response.json()))
#                 ctx.exit(1)
#         else:
#             success(f"'--dry-run' used. Exiting without real update")
#
#     except exceptions.InvalidSchema:
#         error(f"Invalid rancher url '{base_url}'")
#         ctx.exit(1)
#     except exceptions.ConnectionError:
#         error("Unable to connect ", color=True)
#         ctx.exit(1)
#
#
if __name__ == '__main__':
    cli()
