class RancherWorkload:
    def __init__(self, value):
        parts = value.split(":")
        if len(parts) == 3:
            self.type, self.namespace, self.name = parts
        elif len(parts) == 2:
            self.type = "deployment"
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
        parts = value.split(":")
        self.repo = "hub.docker.com"
        self.tag = "latest"
        if len(parts) == 2:
            _image, self.tag = parts
        elif len(parts) == 1:
            _image = parts[0]
        else:
            raise ValueError(value)

        parts = _image.split("/")
        if len(parts) == 3:
            self.repo, self.account, self.image = parts
        elif len(parts) == 2:
            self.account, self.image = parts
        else:
            raise ValueError(value)
        # self.account = parts[0]
        # self.image= "/".join(parts[1:])

        if self.tag:
            self.id = f"{_image}:{self.tag}"
        elif self.image:
            self.id = f"{_image}"
        else:
            raise ValueError(value)

    @property
    def repository(self):
        return f"https://{self.repo}"

    def __repr__(self):
        return self.id
