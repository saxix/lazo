import _thread
import re
import ssl
import time
from functools import wraps
from json import JSONDecodeError
from urllib.parse import urlparse

import websocket
from click import UsageError
from requests import request
from requests.exceptions import SSLError

from lazo.objects import RancherPod
from lazo.types import RancherWorkload

from .exceptions import (
    HttpError,
    InvalidCredentials,
    InvalidName,
    ObjectNotFound,
    ServerConnectionError,
    ServerSSLError, EmptyResponse, LazoError,
)
from .out import echo, error, fail
from .utils import jprint

success_codes = (200, 201, 204)


def on_message(ws, message):
    print(111, message)


def on_error(ws, error):
    print(222, error)


def on_close(ws):
    print(333, "### closed ###")


def on_open(ws):
    def run(*args):
        time.sleep(1)
        ws.close()
        print("thread terminating...")

    _thread.start_new_thread(run, ())


class HttpClient:
    def __init__(self, base_url, *, verify=True, debug=True, auth=None, **kwargs):
        o = urlparse(base_url)
        self.scheme = o.scheme or "http"
        self.port = o.port or {"http": 80, "https": 443}[self.scheme]
        self.scheme = o.scheme
        self.host = o.hostname
        self.path = o.path

        self.base_url = base_url
        self.verify = verify
        self.debug = debug
        self.history = []
        self.auth = auth

    def ping(self) -> bool:
        self.get("/")
        return self.history[-1].status_code == 200

    def _r(self, cmd, url, *, raw=False, ignore_error=False, **kwargs):
        if not (url.startswith("http") or url.startswith("wss")):
            url = f"{self.base_url}{url}"
        try:
            if self.debug:
                print(f"DEBUG: - {cmd} {url}")
            response = request(cmd, url, auth=self.auth, verify=self.verify, **kwargs)
            if response.content == b'null\n':
                raise EmptyResponse(url)
        except SSLError:
            raise ServerSSLError(url)
        except LazoError as e:
            raise
        except Exception as e:
            raise ServerConnectionError(url, e)
        self.history.append(response)

        if response.status_code in success_codes:
            if raw:
                return response
            else:
                try:
                    return response.json()
                except JSONDecodeError as e:
                    raise HttpError(url, response, e)
        elif ignore_error:
            return response
        else:
            raise HttpError(url, response)

    def post(self, url, **kwargs):
        return self._r("post", url, **kwargs)

    def get(self, url, **kwargs):
        return self._r("get", url, **kwargs)

    def delete(self, url, **kwargs):
        return self._r("delete", url, **kwargs)

    def put(self, url, *, data, **kwargs):
        return self._r("put", url, json=data, **kwargs)

    def ws(self, where):
        scheme = "ws" if self.scheme == "http" else "wss"
        base = f"{scheme}://{self.host}:{self.port}"
        url = f"{base}{where}"
        if self.debug:
            echo(f"WS {url}")
        from base64 import b64encode

        userAndPass = b64encode(
            f"{self.auth.username}:{self.auth.password}".encode("utf8")
        ).decode("ascii")
        headers = {"Authorization": "Basic %s" % userAndPass}
        ws = websocket.create_connection(
            url, sslopt={"cert_reqs": ssl.CERT_NONE}, header=headers
        )
        assert ws.connected
        data = []
        while ws.connected:
            rec = ws.recv()
            if rec != b"\x01":
                if isinstance(rec, str):
                    data.append(rec[1:])
                else:
                    data.append(rec[1:].decode("utf8"))

        if not data:
            raise Exception("No response")

        return "".join(data)


class RancherClient(HttpClient):
    def __init__(self, base_url, **kwargs):
        self.use_names = kwargs.pop("use_names", False)
        super().__init__(base_url, **kwargs)
        self._cluster = None
        self._project = None

    def __repr__(self):
        return f"<RancherClient {self.base_url}>"

    @property
    def cluster(self):
        return self._cluster

    @cluster.setter
    def cluster(self, cluster_id):
        if self.use_names:
            cluster_id = self._get_cluster_id_by_name(cluster_id)
        self._cluster = cluster_id

    @property
    def project(self):
        return self._project

    @project.setter
    def project(self, name_or_id):
        if isinstance(name_or_id, (list, tuple)):
            if name_or_id[0]:
                self._cluster = name_or_id[0]
            name = name_or_id[1]
        else:
            name = name_or_id

        if self.use_names:
            name = self._get_project_id_by_name(name)
        self._project = name

    # pods
    def list_pods(self):
        url = f"/project/{self.cluster}:{self.project}/pods?limit=-1&sort=name"
        res = self.get(url)
        return res["data"]

    def get_pod(self, workload: RancherWorkload, elem=1):
        url = f"/project/{self.cluster}:{self.project}/pods?limit=-1&sort=name"
        res = self.get(url)
        for w in res["data"]:
            if w["workloadId"] == workload.id:
                return RancherPod(w)
        raise ObjectNotFound(workload.id)

    # containers
    def list_containers(self):
        url = f"/project/{self.cluster}:{self.project}/containers?limit=-1&sort=name"
        res = self.get(url)
        return res["data"]

    def list_clusters(self):
        res = self.get("/clusters")
        return [(e["name"], e["id"]) for e in res["data"]]

    def list_projects(self):
        response = self.get(f"/clusters/{self.cluster}/projects")
        return [(e["name"], e["id"]) for e in response["data"]]

    def list_workloads(self):
        response = self.get(f"/projects/{self.cluster}:{self.project}/workloads")
        return [(e["name"], e["id"]) for e in response["data"]]

    def get_workload(self, name):
        response = self.get(f"/projects/{self.cluster}:{self.project}/workloads/{name}")
        return response

    def upgrade(self, workload, image, env=None):
        url = f"/project/{self.cluster}:{self.project}/workloads/{workload.id}"
        response = self.get(url)
        if not response:
            return
        json = response.copy()
        found = set()
        if env:
            environment = [{
                "name": k,
                "type": "/v3/project/schemas/envVar",
                "value": v
            } for k, v in dict(env).items()]
            if 'containers' in response:
                for pod in json['containers']:
                    found.add(pod['image'])
                    pod['image'] = image.id
                    if 'env' in pod:
                        pod['env'] = pod['env'] + environment
                    else:
                        pod['env'] = environment

        return self.put(url, data=json)

    def _get_cluster_id_by_name(self, name):
        res = self.get("/clusters")
        for entry in res["data"]:
            if entry["name"] == name:
                return entry["id"]
        raise InvalidName(f"Invalid cluster name '{name}'")

    def _get_project_id_by_name(self, name):
        res = self.get(f"/clusters/{self.cluster}/projects")
        for entry in res["data"]:
            if entry["name"] == name:
                return entry["id"].split(":")[1]
        raise InvalidName(f"Invalid project name '{name}'")

    def _get_workload_id_by_name(self, project, name):
        response = self.get(f"/projects/{self.cluster}:{self.project}/workloads")
        for workload in response["data"]:
            if workload["name"] == name[-1]:
                return workload["id"].split(":")
        raise InvalidName(f"Invalid workload name '{':'.join(name)}'")


class DockerClient(HttpClient):
    def __init__(self, base_url, *, username=None, password=None, **kwargs) -> None:
        super().__init__(base_url, **kwargs)
        self.username = username
        self.password = password

    def __repr__(self):
        return f"<DockerClient {self.base_url}>"

    def exists(self, image):
        try:
            self.get(f"/repositories/{image.image}/tags/{image.tag}/")
            return True
        except HttpError:
            return False

    def login(self):
        url = "/users/login/"
        self.post(
            url,
            json={"username": self.username, "password": self.password},
            ignore_error=True,
        )
        response = self.history[-1]
        if response.status_code == 400:
            raise InvalidCredentials(url, response)
        self.token = response.json()["token"]
        return self.token

    def get_tags(self, image, filter=".*", max_pages=None):
        ret = []
        url = f"/repositories/{image.image}/tags/"
        rex = re.compile(filter)
        page = 1
        while url:
            # TODO: remove me
            print(111, "clients.py:272", url)
            response = self.get(url)
            for e in response["results"]:
                if rex.search(e["name"]):
                    yield e
            if max_pages and page > max_pages:
                break
            url = response["next"]
        return sorted(ret)


def handle_lazo_error(func):
    @wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ServerSSLError as e:
            fail(e)
        except UsageError as e:
            error(e)
        except HttpError as e:
            data = e.response.json()
            error(e.url)
            jprint(data)
        except LazoError as e:
            error(str(e))
        except ServerConnectionError as e:
            error(str(e))
            error(str(e.reason))

    return inner
