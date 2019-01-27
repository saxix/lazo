import importlib
import json

import requests
from pygments import highlight
from pygments.formatters.terminal import TerminalFormatter
from pygments.lexers.data import JsonLexer
# 
# 
# def tag_exists(repository, user, image, tag):
#     url = f'{repository}/v2/repositories/{user}/{image}/tags/{tag}/'
#     response = requests.get(url)
#     return response.status_code == 200
# 
# 
# def get_available_tags(repository, account, image):
#     url = f"{repository}/v2/repositories/{account}/{image}/tags/"
#     response = requests.get(url)
#     if response.status_code == 200:
#         json = response.json()
#         return [e['name'] for e in json['results']]
#     return None
# 
# 
# def get_available_images(repository, account):
#     url = f"{repository}/v2/repositories/{account}/"
#     response = requests.get(url)
#     if response.status_code == 200:
#         json = response.json()
#         return [e['name'] for e in json['results']]
#     return None
# 
#
# def get_target(ctx, repository, base, verbosity, ignore_tag=False):
#     error = partial(printer, 0, verbosity, 'red')
#     success = partial(printer, 0, verbosity, 'green')
#
#     account, docker_image, docker_tag = base
#     if docker_image:
#         tags = get_available_tags(repository, account, docker_image)
#         if tags:
#             if ignore_tag or docker_tag not in tags:
#                 success(f"Available tags are: {', '.join(tags)}")
#                 ctx.exit(1)
#             else:
#                 return account, docker_image, docker_tag
#         else:
#             error("No tags found. Get available images")
#             error(f"Image '{docker_image}' not found on {repository}")
#
#     images = get_available_images(repository, account)
#     if images:
#         success(f"Available images are: {', '.join(images)}")
#         ctx.exit(1)
#     else:
#         error(f"No images found for account '{account}'")
#
#     return account, docker_image, docker_tag


def import_by_name(name):
    """dynamically load a class from a string

    es:
        klass = import_by_name('my_package.my_module.my_class')
        some_object = klass()

    :param name:
    :return:

    """
    if '.' not in name:
        raise ValueError("Cannot import '{}'".format(name))
    class_data = name.split(".")
    module_path = ".".join(class_data[:-1])
    class_str = class_data[-1]
    module = importlib.import_module(module_path)
    try:
        return getattr(module, class_str)
    except AttributeError:
        raise AttributeError('Unable to import {}. '
                             '{} does not have {} attribute'.format(name,
                                                                    module,
                                                                    class_str))


def jprint(obj):
    formatted_json = json.dumps(obj, sort_keys=True, indent=4)
    colorful_json = highlight(formatted_json, JsonLexer(), TerminalFormatter())
    print(colorful_json)
