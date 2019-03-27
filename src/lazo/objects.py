import re


class RancherWorkload:
    def __init__(self, value):
        parts = value.split(':')
        if len(parts) == 3:
            self.type, self.namespace, self.name = parts
        elif len(parts) == 2:
            self.type = 'deployment'
            self.namespace, self.name = parts
        else:
            raise Exception("Invalid workload")
        self.id = ":".join([self.type, self.namespace, self.name])

    def __repr__(self):
        return self.id


class RancherPod:
    def __init__(self, values):
        self.workload = RancherWorkload(values["workloadId"])
        self.id = values["id"]
        self.name = self.id.split(":")[1]

    def __repr__(self):
        return self.id


class DockerImage:
    def __init__(self, value, partial=False):
        rex = re.compile(r"(?P<account>\w*)/?(?P<image>[\w-]*):?(?P<tag>[\w\.-]*)")
        m = rex.match(value)
        self.account, self.image, self.tag = m.groups()
        if self.tag and not self.image:
            raise Exception("Tag needs and image")
        if self.tag:
            self.id = f"{self.account}/{self.image}:{self.tag}"
        elif self.image:
            self.id = f"{self.account}/{self.image}"
        else:
            raise ValueError(value)

        #     self.id = self.account

    def __repr__(self):
        return self.id
