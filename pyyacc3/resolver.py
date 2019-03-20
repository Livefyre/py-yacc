import collections
import os
import re
import sys
from logging import getLogger

from pyyacc3.yml import load
from pyyacc3.yml.extensions import EnvVar

LOG = getLogger(__name__)


class Resolver(object):
    PYYACC_RESOLVER__OVERLAYS = "YACC_RESOLVER__OVERLAYS"

    PYYACC_RESOLVER__ENV_PREFIX = "YACC_RESOLVER__ENV_PREFIX"

    def __init__(self,
                 wdir,
                 env_prefix="YACC",
                 default_env_overlay="YACC__OVERLAY"):
        self.wdir = wdir
        self.default_env_overlay = default_env_overlay
        self.env_prefix = env_prefix

    def assemble(self, descriptor, provided_overlays, ignore_environment=False):
        list(map(descriptor.merge, provided_overlays))
        if not ignore_environment:
            list(map(descriptor.merge, self.get_extra_overlays()))
            descriptor.merge(
                self.get_env_overlay(
                    [(s, k) for s, k, _ in descriptor.specs()]))

    def finalize(self, descriptor):

        def _final(section_key_spec):
            (section, key, spec) = section_key_spec
            LOG.debug("before - %s.%s=%s", section, key, spec.value)
            if isinstance(spec.value, EnvVar):
                spec.value = spec.value.resolve(None)

            spec.value = value = spec.coerce(spec.value)
            err = spec.validate(value, fail=False)
            if err:
                spec.error = err
            LOG.debug("after - %s.%s=%s (%s)", section, key, spec.value, err)

        list(map(_final, descriptor.specs()))

    def get_extra_overlays(self):
        extra_overlays = os.environ.get(self.PYYACC_RESOLVER__OVERLAYS)
        if not extra_overlays:
            extra_overlays = [EnvVar(self.default_env_overlay)]
        else:
            extra_overlays = load(extra_overlays)
        return [_f for _f in map(self._read, extra_overlays) if _f]

    def get_env_overlay(self, section_key_list):
        """
        :type Iterable[(str, str)] section_key_list: (section, key) tuples
        """
        overlay = collections.defaultdict(dict)
        for section, key in section_key_list:
            present, value = self.resolve_env_key(section, key)
            if present:
                overlay[section][key] = value
        return overlay

    def resolve_env_key(self, section, key):
        env_name = re.sub(
            r'[^a-z0-9]',
            '_',
            "%s__%s__%s" % (self.env_prefix, section, key),
            flags=re.I).upper()
        var = EnvVar(env_name)

        try:
            value = var.resolve()
            LOG.debug("found `%s` in environment", env_name)
            return True, value
        except KeyError:
            return False, None

    def _read(self, desc):
        if isinstance(desc, EnvVar):
            resolved = desc.resolve(self)
            if resolved is self:
                LOG.debug("environment overlay `%s` is empty", desc)
                return None
            LOG.debug("environment overlay `%s` resolved", desc)
            return resolved

        assert isinstance(desc, str)
        return self.read_file(desc)

    def read_file(self, fn):
        if fn == "-":
            return load(sys.stdin.read())
        filename = os.path.expanduser(os.path.expandvars(fn))
        try:
            filename = list(
                filter(os.path.exists,
                       [filename, os.path.join(self.wdir, filename)]))[0]
        except IndexError:
            raise IOError("%s does not exist (wd: %s)." % (filename, self.wdir))
        try:
            LOG.debug("loading %s...", filename)
            with open(filename) as fh:
                return load(fh)
        except:
            LOG.error("Error reading file %s", filename)
            raise
