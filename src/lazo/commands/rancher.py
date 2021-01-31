import sys
import urllib

import click
from click import argument

from ..__cli__ import cli
from ..clients import DockerClient, RancherClient, handle_lazo_error
from ..out import echo, error, success
from ..params import (CLUSTER, PROJECT, _docker_options, _global_options,
                      _rancher_options, make_option, options,)
from ..types import DockerImage, Image, RancherWorkload, Workload
from ..utils import jprint, prepare_command


@cli.group()
@options(_global_options, _rancher_options)
@click.pass_context
def rancher(ctx, base_url, insecure, auth, use_names, debug, **kwargs):
    ctx.obj['client'] = RancherClient(base_url, auth=auth,
                                      verify=not insecure,
                                      use_names=use_names,
                                      debug=ctx.find_root().command.debug)


@rancher.command()
@click.pass_context
@handle_lazo_error
def ping(ctx, **kwargs):
    client = ctx.obj['client']
    if client.ping():
        success("Success")
    else:
        error("Fail")


@rancher.command()
@click.pass_context
@handle_lazo_error
def settings(ctx, **kwargs):
    client = ctx.obj['client']
    ret = client.get('/settings')
    jprint(ret)


@rancher.command()
@click.pass_context
@handle_lazo_error
def login(ctx, **kwargs):
    client = ctx.obj['client']
    if client.ping():
        success(f"Successfully logged in to {client.base_url}")
    else:
        error("Fail")


@rancher.command()
@options(_global_options)
@options([CLUSTER, PROJECT])
@click.option('-w',
              '--workload',
              type=Workload,
              help='Rancher workload.',
              metavar='TEXT')
@click.pass_context
@handle_lazo_error
def info(ctx, cluster, project, workload: RancherWorkload, verbosity, **kwargs):
    client = ctx.obj['client']

    client.cluster = cluster
    if project:
        client.project = project

    if workload:
        echo('Workload infos:')
        info = client.get_workload(workload.id)
        if 'containers' in info:
            for e in info['containers']:
                echo("Image:", e['image'])
                echo("imagePullPolicy:", e['imagePullPolicy'])
        if 'publicEndpoints' in info:
            for e in info['publicEndpoints']:
                echo("Ingress:", e['ingressId'])
                echo("Hostname:", e['hostname'])
    elif project:
        echo('Project workloads:')
        for workload in client.list_workloads():
            echo(f"\t{workload[0]:>20}    {workload[1]:<40}")
    elif cluster:
        response = client.get(f'/clusters/{client.cluster}/projects')
        echo(f'Projects on cluster: {client.cluster}')
        for project in response['data']:
            echo(f"\t{project['name']:>15}    {project['id']:<40}")
    else:
        echo('Clusters:')
        for entry in client.list_clusters():
            echo(f"\t{entry[0]:>20}   {entry[1]:<40}")


@rancher.command()
@options([CLUSTER, PROJECT])
@click.pass_context
def pods(ctx, cluster, project):
    client = ctx.obj['client']
    client.cluster = cluster
    client.project = project
    ret = client.list_pods()
    for w in ret:
        echo(f'{w["workloadId"]:<50} {w["id"]}')


@rancher.command()
@options([CLUSTER, PROJECT])
@click.pass_context
def containers(ctx, cluster, project):
    client = ctx.obj['client']
    client.cluster = cluster
    client.project = project
    ret = client.list_containers()
    for w in ret:
        # TODO: remove me
        print(111, "rancher.py:120", w)
        # echo(f'{w["workloadId"]:<50} {w["id"]}')
        # for c in w["containers"]:
        #     echo(f'\t{c["id"]}')
    # jprint(ret)


@rancher.command()
@options(_global_options, _docker_options)
@options([CLUSTER, PROJECT])
@make_option('--workload', '-w', 'workloads', type=Workload, metavar='WORKLOAD', required=True, multiple=True)
@make_option('--image', '-i', type=Image, metavar='IMAGE', required=True, )
@make_option('--check/--no-check', is_flag=True, default=True)
@click.pass_context
@handle_lazo_error
def upgrade(ctx, cluster, project, workloads: [RancherWorkload], image: DockerImage, check,
            repository, username, password, **kwargs):
    client = ctx.obj['client']
    if check:
        if not repository:
            repository = image.repository
        docker = DockerClient(repository, username=username, password=password)
        if not docker.exists(image):
            error(f"Cannot find image '{image.id}' on {repository}")
            error(f"Run lazo docker info '{image.id}' to check available tags")
            sys.exit(1)
    client.cluster = cluster
    client.project = project
    # namespace, workload_name = workload

    for workload in workloads:
        echo(f"Upgrading workload '{workload.id}' on project '{client.cluster}:{client.project}' to '{image.id}'")

        client.upgrade(workload, image)
        info = client.get_workload(workload)
        if 'containers' in info:
            for e in info['containers']:
                echo("Image:", e['image'])
        if 'publicEndpoints' in info and info['publicEndpoints']:
            for ep in info['publicEndpoints']:
                echo("Ingress:", ep['ingressId'])
                echo("Hostname:", ep.get('hostname', ''))


@rancher.command()
@options(_global_options, _docker_options)
@options([CLUSTER, PROJECT])
@argument('workload', type=Workload, metavar='NAME')
@argument('command', nargs=-1)
# @make_option('-c', '--check', is_flag=True)
# @make_option('-c', '--dry-run', is_flag=True)
@click.pass_context
@handle_lazo_error
def shell(ctx, cluster, project, workload: RancherWorkload, command, **kwargs):
    client = ctx.obj['client']
    client.cluster = cluster
    client.project = project
    pod = client.get_pod(workload)
    cmds = [('container', pod.workload.name),
            ('stdin', '1'),
            ('stdout', '1'),
            ('stderr', '1'),
            ('tty', '1'),
            ]
    cmds.extend(prepare_command(command))
    qs = urllib.parse.urlencode(cmds)
    try:
        url = f'/k8s/clusters/{client.cluster}/api/v1/namespaces/{workload.namespace}/pods/{pod.name}/exec?{qs}'
        ret = client.ws(url)
    except Exception as e:
        error(e)
        sys.exit(1)

    print(ret)
