class ComponentRegistry:
    def __init__(self):
        self._providers = {}

    def register(self, usage, provider_type, provider_class):
        self._providers[(usage, provider_type)] = provider_class

    def get(self, usage, provider_type):
        return self._providers.get((usage, provider_type))

    def build(self, env, usage, provider_type):
        provider_class = self.get(usage, provider_type)
        if not provider_class:
            return None
        return provider_class(env)


registry = ComponentRegistry()

