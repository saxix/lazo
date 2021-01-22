import sys

import click

from ..__cli__ import cli
from ..clients import DockerClient, handle_lazo_error
from ..exceptions import HttpError
from ..out import echo, error, success
from ..params import _docker_options, _global_options, make_option, options
from ..types import Image
from ..utils import jprint, sizeof


@cli.group()
@options(_global_options)
@click.pass_context
def docker(ctx, **kwargs):
    pass
    # if stdin:
    #     username, password = stdin
    # ctx.obj['client'] = DockerClient(repository,
    #                                  username=username, password=password,
    #                                  debug=ctx.find_root().command.debug)


@docker.command()
@options(_global_options, _docker_options)
@click.argument("image", type=Image, metavar='IMAGE')
@click.option("--filter", metavar='REGEX', default='.*')
@click.option("--size", is_flag=True)
@click.pass_context
def info(ctx, image, filter, size, repository, username, password, stdin, **kwargs):
    client = DockerClient(repository,
                          username=username, password=password,
                          debug=ctx.find_root().command.debug)

    client.base_url = image.repository
    try:
        if image.tag:
            response = client.get(f'/repositories/{image.image}/tags/{image.tag}/')
            jprint(response)
        elif image.image:
            for tag in client.get_tags(image, filter):
                if size:
                    echo(f"{tag['name']:<30} {sizeof(tag['full_size'])}")
                else:
                    echo(tag['name'])

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
@make_option("--no-input", is_flag=True)
@click.pass_context
@handle_lazo_error
def rm(ctx, image, no_input, **kwargs):
    client = ctx.obj['client']
    if image.tag:
        if client.exists(image):
            msg = """THIS IS A UNRECOVERABLE ACTION.

Continuing will irremediably remove image '%s' from the server.
Be sure to have a local copy.

Do you want to continue? """

            if no_input or click.confirm(msg % image.id):
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
