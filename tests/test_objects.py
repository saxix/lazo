import pytest

from lazo.objects import RancherWorkload, RancherPod, DockerImage
from lazo.utils import sizeof, import_by_name


def test_rancherworkload():
    w = RancherWorkload("ns:name")
    assert w.type == 'deployment'
    assert w.namespace == 'ns'
    assert w.name == 'name'
    assert w.id == 'deployment:ns:name'


def test_rancherworkload_fullname():
    w = RancherWorkload("type:ns:name")
    assert w.type == 'type'
    assert w.namespace == 'ns'
    assert w.name == 'name'
    assert w.id == 'type:ns:name'


def test_rancherworkload_error():
    with pytest.raises(Exception):
        RancherWorkload("name")


def test_rancherpod():
    pod = RancherPod({"workloadId": "bitcaster:adminer",
                      "id": "bitcaster:adminer-659dc68d84-ncdw4"})
    assert pod.name == 'adminer-659dc68d84-ncdw4'
    assert pod.id == 'bitcaster:adminer-659dc68d84-ncdw4'


def test_dockerimage():
    i = DockerImage("bitcaster/bitcaster:1.0")
    assert i.account == 'bitcaster'
    assert i.image == 'bitcaster'
    assert i.tag == '1.0'


def test_dockerimage_default():
    i = DockerImage("bitcaster/bitcaster")
    assert i.account == 'bitcaster'
    assert i.image == 'bitcaster'
    assert i.tag == 'latest'


def test_dockerimage_customrepo():
    i = DockerImage("gilab.com/bitcaster/bitcaster")
    assert i.repo == 'gilab.com'
    assert i.account == 'bitcaster'
    assert i.image == 'bitcaster'
    assert i.tag == 'latest'


def test_dockerimage_account():
    with pytest.raises(ValueError):
        DockerImage("bitcaster")


def test_dockerimage_error():
    with pytest.raises(Exception):
        DockerImage("bitcaster:1.0")
