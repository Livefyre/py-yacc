import collections
from collections import defaultdict
from logging import getLogger

from pyyacc3.yml.extensions import ValueSpec

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
            if mapping[section] is None:
                LOG.debug("%s is null.", section)
                continue
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

        def _collect(section_key_spec):
            section, key, spec = section_key_spec
            if spec.error:
                errors.append((section, key, spec.error))
                return
            elif spec.optional and spec.value is None:
                return
            else:
                val = spec.value
            overlay[section][key] = spec.coerce(val)

        list(map(_collect, self.specs()))
        return errors, dict(**overlay)

    def merge(self, overlay):
        """
        :param Dict[str, Dict[str, *]] overlay: values to merge.
        """
        for section in [s for s in list(overlay.keys()) if s in self]:
            for key in [
                    k for k in list(overlay[section].keys())
                    if k in self[section]
            ]:
                self[section][key].value = overlay[section][key]
