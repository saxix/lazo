import importlib
import json

from pygments import highlight
from pygments.formatters.terminal import TerminalFormatter
from pygments.lexers.data import JsonLexer


# def sizeof(num, suffix="B"):
#     for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
#         if abs(num) < 1024.0:
#             return "%3.1f%s%s" % (num, unit, suffix)
#         num /= 1024.0
#     return "%.1f%s%s" % (num, "Yi", suffix)


# def import_by_name(name):
#     """dynamically load a class from a string
#
#     es:
#         klass = import_by_name('my_package.my_module.my_class')
#         some_object = klass()
#
#     :param name:
#     :return:
#
#     """
#     if "." not in name:
#         raise ValueError("Cannot import '{}'".format(name))
#     class_data = name.split(".")
#     module_path = ".".join(class_data[:-1])
#     class_str = class_data[-1]
#     module = importlib.import_module(module_path)
#     try:
#         return getattr(module, class_str)
#     except AttributeError:
#         raise AttributeError(
#             "Unable to import {}. "
#             "{} does not have {} attribute".format(name, module, class_str)
#         )


def jprint(obj, colors=True):
    formatted_json = json.dumps(obj, sort_keys=True, indent=4)
    if colors:
        colorful_json = highlight(formatted_json, JsonLexer(), TerminalFormatter())
        print(colorful_json)
    else:
        print(formatted_json)


def prepare_command(cmds):
    if not isinstance(cmds, (list, tuple)):
        cmds = cmds.split()
    return list(zip(["command"] * len(cmds), cmds))
