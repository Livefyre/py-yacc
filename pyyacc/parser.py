from logging import getLogger

from pyyacc.yml import load, dump
from pyyacc.yml.extensions import ValueSpec, \
    Optional, ConfigRoot


LOG = getLogger(__name__)


class ConfigBuilder(object):
    """A structure which defines the configuration specification."""

    def __init__(self, descriptor):
        """
        :param ConfigRoot descriptor:
        """
        self.descriptor = descriptor

    def validate(self, params):
        return self.descriptor.validate(params)

    def build(self, *overlays):
        """
        Assemble a configuration with the provided overlays.

        :param [dict] overlays: A list of overlays, where the last overlay value is selected.
        :returns: dict
        """
        params = {}
        for section in self.descriptor.keys():
            params[section] = {}
            for key, setting in self.descriptor[section].items():
                if not isinstance(setting, ValueSpec):
                    LOG.debug("ignoring non-spec value for '%s': %s", key, setting)
                    continue
                v = self._resolve_value(overlays, section, key, setting)
                if isinstance(v, Optional):
                    LOG.debug("%s.%s is optional, but not defined, skipping", section, key)
                    continue
                params[section][key] = v
        return params

    def _resolve_value(self, overlays, section, key, setting):
        value = setting.value
        for i, o in enumerate(overlays):
            if key in o.get(section, {}):
                value = o[section][key]
                LOG.debug("%s.%s found in overlay %d", section, key, i)
        return setting.coerce(value)

    @classmethod
    def parse(cls, *files):
        """
        Takes a list of config yaml files; assumes the first is the descriptor, and
        builds up a config set.
        """
        if not files:
            raise ValueError("no inputs")

        def parse(fn):
            if isinstance(fn, dict):
                return ConfigRoot(fn)
            if isinstance(fn, basestring):
                LOG.debug("loading %s", fn)
                fn = open(fn)
            v = load(fn)
            if v is None:
                v = {}
            return ConfigRoot(v)

        roots = map(parse, files)
        desc = roots.pop(0)
        builder = cls(desc)
        params = builder.build(*roots)
        return builder, params


def unparse(stream, params, **kwargs):
    """Serialize the parameters to the stream as YAML."""
    dump(params, stream, **kwargs)


def build(*files):
    """Legacy interface."""
    return ConfigBuilder.parse(*files)
