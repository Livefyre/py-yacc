import logging
import re
import os

LOG = logging.getLogger(__name__)
CREDENTIAL_MIMETYPE = "application/vnd.pyyacc.credential"


class CredentialBackend:
    def __init__(self, resolver):
        self.resolvers = [resolver]

    def add_resolver(self, r):
        self.resolvers.insert(0, r)

    def get(self, credential):
        for r in self.resolvers:
            value = r.get(credential)
            if value is not None:
                return value


class DefaultResolver:
    def get(self, credential):
        return str(credential)


class EnvironmentResolver:
    """Resolve values from the environment."""
    def clean(self, value):
        return re.sub(r'[^a-z0-9]', '_', value, flags=re.I)

    def get(self, credential):
        """

        :param DataURI credential:
        """
        if 'name' in credential.parameters and 'provider' in credential.parameters:
            key = self.clean('%s__%s' %
                             (credential.parameters['provider'], credential.parameters['name']))
            if key in os.environ:
                LOG.info("resolved %s from the environment" % key)
                return os.environ[key]


CredentialStore = CredentialBackend(DefaultResolver())
