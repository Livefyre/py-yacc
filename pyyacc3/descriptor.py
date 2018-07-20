from logging import getLogger
from pyyacc3.yml.extensions import ValueSpec
from collections import defaultdict
import collections

LOG = getLogger(__name__)


class YaccDescriptor(defaultdict):
    """A descriptor, as a collection of ValueSpecs"""

    def __init__(self, mapping):
        """
        :param str wdir: working directory
        :param Dict[str, Dict[str, ValueSpec]] descriptors:
        """
        assert isinstance(mapping, dict)
        super(YaccDescriptor, self).__init__(dict)
        for section in mapping:
            for key, spec in mapping[section].items():
                if not isinstance(spec, ValueSpec):
                    LOG.debug("%s.%s is not a ValueSpec", section, key)
                    continue
                self[section][key] = spec

    def specs(self):
        """
        :rtype: Iterator[str, str, :class:`ValueSpec`]
        """
        for section in self.keys():
            for key, spec in self[section].items():
                yield section, key, spec

    def collect(self):
        overlay = collections.defaultdict(dict)
        errors = []

        def _collect((section, key, spec)):
            if spec.error:
                errors.append((section, key, spec.error))
                return
            elif spec.optional and spec.value is None:
                return
            else:
                val = spec.value
            overlay[section][key] = spec.coerce(val)

        map(_collect, self.specs())
        return errors, dict(**overlay)

    def merge(self, overlay):
        """
        :param Dict[str, Dict[str, *]] overlay: values to merge.
        """
        for section in filter(lambda s: s in self, overlay.keys()):
            for key in filter(lambda k: k in self[section], overlay[section].keys()):
                self[section][key].value = overlay[section][key]
