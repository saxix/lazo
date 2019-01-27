import sys

import click

from lazo.clients import DockerClient, handle_http_error
from lazo.exceptions import HttpError
from lazo.out import echo, error, success
from lazo.params import _docker_options, _global_options, options
from lazo.types import Image
from lazo.utils import jprint

from ..__cli__ import cli


@cli.group()
@options(_global_options, _docker_options)
@click.pass_context
def docker(ctx, repository, username, password, stdin, **kwargs):
    if stdin:
        username, password = stdin
    ctx.obj['client'] = DockerClient(repository,
                                     username=username, password=password,
                                     debug=ctx.find_root().command.debug)


@docker.command()
@options(_global_options)
@click.argument("image", type=Image, metavar='IMAGE')
@click.pass_context
def info(ctx, image, **kwargs):
    client = ctx.obj['client']
    try:
        if image.tag:
            response = client.get(f'/repositories/{image.account}/{image.image}/tags/{image.tag}/')
            jprint(response)
        elif image.image:
            response = client.get(f'/repositories/{image.account}/{image.image}/tags/')
            for e in response['results']:
                echo(e['name'])
        elif image.account:
            response = client.get(f'/repositories/{image.account}/')
            for e in response['results']:
                echo(e['name'])
    except HttpError as e:
        error(str(e))
        sys.exit(1)


@docker.command()
@click.pass_context
def ping(ctx, **kwargs):
    client = ctx.obj['client']
    if client.ping():
        click.echo("Success")


@docker.command()
@options(_global_options)
@click.argument("image", type=Image, metavar='IMAGE')
@click.option("--no-input", is_flag=True)
@click.pass_context
@handle_http_error
def rm(ctx, image, no_input, **kwargs):
    client = ctx.obj['client']
    if image.tag:
        if client.exists(image):
            msg = """THIS IS A UNRECOVERABLE ACTION.
            
Continuing will irremediably remove image '%s' from the server.  
Be sure to have a local copy.

Do you want to continue? """

            if no_input or click.confirm(msg % image.id ):
                token = client.login()
                response = client.delete(f'/repositories/{image.account}/{image.image}/tags/{image.tag}/',
                                         raw=True,
                                         headers={'Authorization': f'JWT {token}'})
                if response.status_code == 204:
                    success("Deleted")
            else:
                error("Aborted")
        else:
            error("Tag does not exists")
    else:
        error(f"Cannot find {image.id}")
