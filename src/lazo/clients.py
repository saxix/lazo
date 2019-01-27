import sys
from functools import wraps
from json import JSONDecodeError

from requests import request

from lazo.exceptions import ConnectionError, HttpError, InvalidCredentials, Http404, InvalidName
from lazo.out import error, echo
from lazo.utils import jprint

success_codes = (200, 201, 204)


class HttpClient:
    def __init__(self, base_url, *, verify=True, debug=False, auth=None, **kwargs):
        self.base_url = base_url
        self.verify = verify
        self.debug = debug
        self.history = []
        self.auth = auth

    def ping(self) -> bool:
        self.get('/')
        return self.history[-1].status_code == 200

    def _r(self, cmd, url, *, raw=False, ignore_error=False, **kwargs):
        url = f"{self.base_url}{url}"
        try:
            if self.debug:
                echo(f"{cmd} {url}")
            response = request(cmd, url, auth=self.auth, verify=self.verify, **kwargs)
        except Exception as e:
            raise ConnectionError(url, e)
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
        return self._r('post', url, **kwargs)

    def get(self, url, **kwargs):
        return self._r('get', url, **kwargs)

    def delete(self, url, **kwargs):
        return self._r('delete', url, **kwargs)

    def put(self, url, data, **kwargs):
        return self._r('delete', url, json=data, **kwargs)

        # response = requests.put(url, json=data, auth=self.auth, verify=self.verify)
        # self.history.append(response)
        # return response.json()


class RancherClient(HttpClient):
    def __init__(self, base_url, **kwargs):
        super().__init__(base_url, **kwargs)

    def __repr__(self):
        return f"<RancherClient {self.base_url}>"

    def get_cluster_id_by_name(self, name):
        res = self.get('/clusters')
        for entry in res['data']:
            if entry['name'] == name:
                return entry['id']
        raise InvalidName(f"Invalid cluster name '{name}'")

    def get_project_id_by_name(self, name):
        cluster, project = name
        cluster_id = self.get_cluster_id_by_name(cluster)
        res = self.get(f'/clusters/{cluster_id}/projects')
        for entry in res['data']:
            if entry['name'] == project:
                return entry['id'].split(":")
        raise InvalidName(f"Invalid project name '{name}'")

    def get_workload_id_by_name(self, project, name):
        cluster, project = self.get_project_id_by_name(project)
        response = self.get(f'/projects/{cluster}:{project}/workloads')
        for workload in response['data']:
            if workload['name'] == name[-1]:
                return cluster, project, workload['id'].split(":")

        # cluster_id = self.get_cluster_id_by_name(cluster)
        # res = self.get(f'/clusters/{cluster_id}/projects')
        # for entry in res['data']:
        #     if entry['name'] == project:
        #         return entry['id'].split(":")
        raise InvalidName(f"Invalid workload name '{name}'")


class DockerClient(HttpClient):

    def __init__(self, base_url, *, username=None, password=None, **kwargs) -> None:
        super().__init__(base_url, **kwargs)
        self.username = username
        self.password = password

    def __repr__(self):
        return f"<DockerClient {self.base_url}>"

    def exists(self, image):
        try:
            self.get(f'/repositories/{image.account}/{image.image}/tags/{image.tag}/')
            return True
        except HttpError:
            return False

    def login(self):
        url = '/users/login/'
        self.post(url, json={"username": self.username,
                             "password": self.password},
                  ignore_error=True)
        response = self.history[-1]
        if response.status_code == 400:
            raise InvalidCredentials(url, response)
        self.token = response.json()['token']
        return self.token


def handle_http_error(func):
    @wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (HttpError, ConnectionError) as e:
            error(str(e))
            sys.exit(1)

    return inner
