from click import BadParameter, UsageError


class LazoError(Exception):
    pass

class ServerConnectionError(LazoError):
    def __init__(self, url, exc=None):
        self.url = url
        self.reason = exc

    def __str__(self):
        return f"{self.url}. {str(self.reason or '')}"


class ServerSSLError(ServerConnectionError):
    def __str__(self):
        return "Certificate verify failed. Try to use --insecure"


class HttpError(LazoError):
    def __init__(self, url, response, exc=None):
        self.url = url
        self.response = response
        self.exc = exc

    def __str__(self):
        return f"{self.response.status_code}: {self.url}. {str(self.exc or '')}"

class EmptyResponse(LazoError):
    def __init__(self, message, exc=None):
        self.message = message
    def __str__(self):
        return f"Empty Response: {self.message}"


class Http404(HttpError):
    pass


class InvalidName(UsageError):
    def __init__(self, name):
        self.name = name
        self.message = name


class InvalidCredentials(HttpError):
    def __str__(self):
        return "Invalid credential"


class RequiredParameter(UsageError):
    pass


class ExBadParameter(BadParameter):
    def format_message(self):
        return self.message


class ObjectNotFound(Exception):
    pass
