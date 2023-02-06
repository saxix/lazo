import pytest

from lazo.clients import RancherClient
from lazo.objects import DockerImage, RancherWorkload


@pytest.fixture
def client() -> RancherClient:
    return RancherClient(
        base_url="https://rancher/v3",
        cluster="cluster",
        project="project",
        debug=False,
    )


def test_ping(client: RancherClient, mocked_responses):
    mocked_responses.add(
        mocked_responses.GET,
        "https://rancher/v3/",
        json={
            "apiVersion": {
                "group": "management.cattle.io",
                "path": "/v3",
                "version": "v3",
            }
        },
    )
    assert client.ping()


def test_list_workloads(client: RancherClient, mocked_responses):
    mocked_responses.add(
        mocked_responses.GET,
        "https://rancher/v3/projects/cluster:project/workloads",
        json={
            "data": [
                {
                    "name": "workload1",
                    "id": "deployment:namespace:workload1",
                },
                {
                    "name": "workload2",
                    "id": "deployment:namespace:workload2",
                },
            ]
        },
    )
    assert client.list_workloads()


def test_get_workload(client: RancherClient, mocked_responses):
    mocked_responses.add(
        mocked_responses.GET,
        "https://rancher/v3/projects/cluster:project/workloads/deployment:namespace:beat",
        json={
            "name": "workload2",
            "id": "deployment:namespace:workload2",
        },
    )
    assert client.get_workload("deployment:namespace:beat")


# def test_list_projects(client: RancherClient, mocked_responses):
#     mocked_responses.add(
#         mocked_responses.GET,
#         "https://xavier.sosbob.com/v3/project/local:p-jq778/workloads/deployment:namespace:beat",
#         json={"name": "beat",
#               "namespaceId": "namespace",
#               "type": "deployment",
#               "baseType": "workload"
#               },
#     )
#     assert client.list_projects()


def test_upgrade(client: RancherClient, mocked_responses):
    mocked_responses.add(
        mocked_responses.GET,
        "https://rancher/v3/project/cluster:project/workloads/deployment:namespace:workload",
        json={"containers": [{"image": "aaa"}]},
    )
    mocked_responses.add(
        mocked_responses.PUT,
        "https://rancher/v3/project/cluster:project/workloads/deployment:namespace:workload",
        json={"containers": [{"image": "aaa"}]},
    )
    w = RancherWorkload("namespace:workload")
    assert client.upgrade(w, "image")


def test_upgrade_env(client, mocked_responses):
    mocked_responses.add(
        mocked_responses.GET,
        "https://rancher/v3/project/cluster:project/workloads/deployment:namespace:workload",
        json={
            "containers": [
                {
                    "image": "aaa",
                    "env": [
                        {
                            "name": "ENV1",
                            "type": "/v3/project/schemas/envVar",
                            "value": "0",
                        }
                    ],
                }
            ]
        },
    )
    mocked_responses.add(
        mocked_responses.PUT,
        "https://rancher/v3/project/cluster:project/workloads/deployment:namespace:workload",
        json={
            "containers": [
                {
                    "image": "aaa",
                    "env": [
                        {
                            "name": "ENV1",
                            "type": "/v3/project/schemas/envVar",
                            "value": "0",
                        }
                    ],
                }
            ]
        },
    )
    w = RancherWorkload("namespace:workload")
    i = DockerImage("t/image")
    assert client.upgrade(w, i, env={"ENV1": 22})


def test_get_env(client, mocked_responses):
    mocked_responses.add(
        mocked_responses.GET,
        "https://rancher/v3/projects/cluster:project/workloads/deployment:namespace:workload",
        json={
            "containers": [
                {
                    "image": "aaa",
                    "name": "name",
                    "env": [
                        {
                            "name": "AUTOSTART_DAPHNE",
                            "type": "/v3/project/schemas/envVar",
                            "value": "0",
                        }
                    ],
                }
            ]
        },
    )
    w = RancherWorkload("namespace:workload")
    assert client.get_env(w) == {
        "name": [
            {
                "name": "AUTOSTART_DAPHNE",
                "type": "/v3/project/schemas/envVar",
                "value": "0",
            }
        ]
    }
