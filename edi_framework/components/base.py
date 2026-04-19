class BaseProvider:
    provider_type = None
    usage = None

    def __init__(self, env):
        self.env = env


class BaseSourceProvider(BaseProvider):
    usage = "source"

    def fetch(self, source, context_data=None):
        raise NotImplementedError


class BaseTargetProvider(BaseProvider):
    usage = "target"

    def send(self, target, payload, context_data=None):
        raise NotImplementedError

