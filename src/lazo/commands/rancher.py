import sys

import click
from click import argument

from lazo.clients import RancherClient, handle_http_error
from lazo.exceptions import RequiredParameter
from lazo.out import echo, error, success
from lazo.types import DockerImage, Image, Project, Workload
from lazo.utils import jprint

from ..__cli__ import cli
from ..params import (CLUSTER, PROJECT, WORKLOAD, _global_options,
                      _rancher_options, options, )


@cli.group()
@options(_global_options, _rancher_options)
@click.pass_context
def rancher(ctx, base_url, insecure, auth, use_names, debug, **kwargs):
    ctx.obj['use_names'] = use_names
    ctx.obj['client'] = RancherClient(base_url, auth=auth,
                                      verify=not insecure,
                                      debug=ctx.find_root().command.debug)


@rancher.command()
@click.pass_context
@handle_http_error
def ping(ctx, **kwargs):
    client = ctx.obj['client']
    if client.ping():
        success("Success")
    else:
        error("Fail")


@rancher.command()
@options(_global_options)
@options([CLUSTER, PROJECT, WORKLOAD])
@click.pass_context
@handle_http_error
def info(ctx, cluster, project, workload, verbosity, **kwargs):
    client = ctx.obj['client']
    use_names = ctx.obj['use_names']
    try:
        if workload:
            if use_names:
                cluster, project_id, ids = client.get_workload_id_by_name(project, workload)
                target = ":".join(ids)
            else:
                cluster, project_id = project
                target = ":".join(workload)
            # assert project
            response = client.get(f'/projects/{cluster}:{project_id}/workloads/{target}')
            echo('Workload infos:')
            for entry in response['containers']:
                echo(f"\tImage: {entry['image']}")
                echo(f"\tCommand: {entry['command']}")
                echo(f"\timagePullPolicy: {entry['imagePullPolicy']}")
        elif project:
            cluster, name = project
            if use_names:
                cluster, name = client.get_project_id_by_name(project)
            response = client.get(f'/projects/{cluster}:{name}/workloads')

            echo('Project workloads:')
            for workload in response['data']:
                echo(f"\t{workload['name']:>20}    {workload['id']:<40}")
        elif cluster:
            if use_names:
                cluster = client.get_cluster_id_by_name(cluster)
            response = client.get(f'/clusters/{cluster}/projects')
            echo('Projects on cluster:')
            for project in response['data']:
                echo(f"\t{project['name']:>15}    {project['id']:<40}")
        else:
            res = client.get('/clusters')
            echo('Clusters:')
            for entry in res['data']:
                echo(f"\t{entry['name']:>20}   {entry['id']:<40}")
    except Exception as e:
        error(str(e))
        sys.exit(1)


@rancher.command()
@options(_global_options)
@argument('project',
          type=Project,
          envvar='RANCHER_PROJECT',
          metavar='PROJECT')
@argument('workload',
          type=Workload,
          envvar='RANCHER_WORKLOAD',
          metavar='WORKLOAD')
@argument('image',
          type=Image,
          metavar='IMAGE')
@click.pass_context
@handle_http_error
def upgrade(ctx, project, workload, image: DockerImage, **kwargs):
    use_names = ctx.obj['use_names']
    client = ctx.obj['client']

    if use_names:
        cluster, project_id, ids = client.get_workload_id_by_name(project, workload)
        __, namespace, workload = ids
    else:
        cluster, project_id = project
        __, namespace, workload = workload

    echo(f"Upgrading workload {namespace}:{workload} on project {cluster}:{project_id} to {image.id}")

    url = f'/project/{cluster}:{project_id}/workloads/deployment:{namespace}:{workload}'
    response = client.get(url)
    try:
        found = set()
        if 'containers' in response:
            for pod in response['containers']:
                found.add(pod['image'])
                pod['image'] = image.id
            echo(f"Found {len(response['containers'])} pod(s)")
            echo(f"Existing tags are: {','.join(found)}")
    except Exception as e:
        error(repr(e))

    # log(f"Updating all pod(s) to {image_full_name}")
    # if not dry_run:
    #     response = requests.put(url, json=json, auth=auth, verify=not insecure)
    #     if response.status_code == 200:
    #         success("Success")
    #         ctx.exit(0)
    #     else:
    #         error(f"Error with rancher API at '{url}'")
    #         error(pformat(response.json()))
    #         ctx.exit(1)
    # else:
    #     success(f"'--dry-run' used. Exiting without real update")
