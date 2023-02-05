from urllib.parse import urlparse

import click
from click.types import BoolParamType
from requests.auth import HTTPBasicAuth

from lazo.exceptions import ExBadParameter
from lazo.objects import DockerImage, RancherWorkload


class ExParamType(click.ParamType):
    def rfail(self, message, param=None, ctx=None):
        # message = f"Invalid value for {param}"
        raise ExBadParameter(message, ctx=ctx, param=param)


class UrlParamType(ExParamType):
    def convert(self, value: str, param, ctx):
        try:
            if not value.strip():
                raise ExBadParameter("Url should be empty")
            o = urlparse(value)
            if o.path.endswith("/"):
                raise ExBadParameter("Url should not ends with '/'")
        except Exception:
            raise ExBadParameter(
                "Invalid url. Should be something like 'https://rancher.example.com:9000/v3/'"
            )

        return value


Url = UrlParamType()


class VerbosityParamType(ExParamType):
    name = "verbosity"

    def __init__(self) -> None:
        self.quit = False

    def convert(self, value, param, ctx):
        self.total = value
        if param.name == "quit":
            self.quit = True
        if self.quit:
            value = -1
        return int(value)


Verbosity = VerbosityParamType()

ImagePullPolices = {
    "IfNotPresent": "IfNotPresent",
    "Always": "Always",
    "Never": "Never",
    "ifnotpresent": "IfNotPresent",
    "always": "Always",
    "never": "Never",
    "i": "IfNotPresent",
    "a": "Always",
    "n": "Never",
}


class IChoice(click.Choice):
    def convert(self, value, param, ctx):
        if value in ImagePullPolices:
            value = ImagePullPolices[value]
        return super().convert(value, param, ctx)


class WorkloadParamType(ExParamType):
    def convert(self, value, param, ctx):
        try:
            return RancherWorkload(value)
        except Exception:
            self.rfail(
                f"Invalid  workload name '{value}'. "
                f"Please use the form '[deployment:]namespace:workload' "
            )


Workload = WorkloadParamType()


class ProjectParamType(ExParamType):
    def convert(self, value, param, ctx):
        parts = [None, value]
        try:
            if ":" in value:
                parts = value.split(":")
                assert len(parts) == 2
        except Exception:
            self.rfail(
                f"Invalid value '{value}' for PROJECT. Please indicate project in the form 'clusterId:projectID' "
            )
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
        try:
            return DockerImage(value)
        except Exception as e:
            self.fail(
                f"{e}. Invalid '{value}' Please indicate image in the form 'account[/image[:tag]]' "
            )


Image = ImageParamType()


class DebugModeType(BoolParamType):
    def __call__(self, value, param=None, ctx=None):
        ctx.find_root().command.debug = True
        return True


DebugMode = DebugModeType()


class StdinAuthType(BoolParamType):
    def __call__(self, value, param=None, ctx=None):
        stdin = click.get_text_stream("stdin")
        credentials = stdin.read()
        return credentials.split(":")


StdinAuth = StdinAuthType()
