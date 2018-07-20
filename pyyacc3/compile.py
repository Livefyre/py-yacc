from ConfigParser import ConfigParser
import StringIO
from collections import defaultdict
from contextlib import contextmanager
import itertools
import json
from logging import getLogger
import logging
from optparse import OptionParser
import os
import pickle
import sys

from safeoutput import open as safeopen

from pyyacc3.descriptor import YaccDescriptor
from pyyacc3.resolver import Resolver
from pyyacc3.yml import load, dump


LOG = getLogger(__name__)


class Compiler(object):
    """
    A configuration loader and CLI interface.
    """

    _usage = "usage: %prog [options] yaml [yaml ...]"
    _formats = "yaml, json, sh, make, ini, raw".split(", ")

    # options
    arg_verbose = False
    arg_flat = False  #: :type bool: flatten first level of nesting.
    arg_format = "yaml"
    arg_validate = True
    arg_output = "-"
    arg_overlays = []
    arg_parsed = []
    arg_key = None
    arg_descriptor = None
    arg_env_prefix = "YACC"
    arg_env_overlay = "YACC__OVERLAY"

    # members
    params = None
    errors = None

    def parser(self):
        parser = OptionParser(usage=self._usage)
        parser.add_option("-v", dest="arg_verbose",
                          action="store_const",
                          default=self.arg_verbose,
                          const=logging.INFO,
                          help="Verbose logging output.")
        parser.add_option("-V", dest="arg_verbose",
                          action="store_const",
                          default=self.arg_verbose,
                          const=logging.DEBUG,
                          help="Very verbose logging output.")
        parser.add_option("--flat", dest="arg_flat",
                          action="store_true",
                          default=self.arg_flat,
                          help="Flatten into 'section.key': value notation")
        parser.add_option("-f", "--format", dest="arg_format",
                          default="yaml",
                          choices=self._formats,
                          help="Output format: yaml, json, sh, make are supported.")
        parser.add_option("--no-validate", dest="arg_validate",
                          action="store_false",
                          default=self.arg_validate,
                          help="Disable validation [default: on]")
        parser.add_option("-o", "--output", dest="arg_output",
                          default=self.arg_output,
                          help="Output destination: path where to write output. If not provided, stdout is used.")
        parser.add_option("--env-prefix", dest="arg_env_prefix",
                          default=self.arg_env_prefix,
                          help="Prefix for overlays from the environment")
        parser.add_option("--env-overlay", dest="arg_env_overlay",
                          default=self.arg_env_overlay,
                          help="Name of an overlay to load from the environment")
        parser.add_option("--key", dest="arg_key",
                          default=self.arg_key,
                          help="Output a single key (section.key)")
        return parser

    def init(self, **kwargs):
        for k, v in kwargs.items():
            key = "arg_%s" % k
            if not hasattr(self, key):
                raise ValueError(k)
            setattr(self, key, v)
        return self

    def argparse(self, args=sys.argv[1:]):
        (options, yamls) = self.parser().parse_args(args=args)
        for k in filter(lambda k: k.startswith("arg_"), dir(options)):
            setattr(self, k, getattr(options, k))
        self.arg_overlays = yamls
        if self.arg_verbose:
            logging.basicConfig(stream=sys.stderr, level=self.arg_verbose)

    def load(self):
        try:
            wdir = os.path.dirname(self.arg_overlays[0]) or os.getcwd()
        except:
            wdir = os.getcwd()
        resolver = Resolver(wdir, self.arg_env_prefix, self.arg_env_overlay)

        def parse(fn):
            if isinstance(fn, dict):
                return fn
            if hasattr(fn, 'read'):
                return load(fn.read())
            return resolver.read_file(fn)

        overlays = filter(None, map(parse, self.arg_overlays))

        if not overlays:
            raise ValueError("No valid descriptor or overlays provided: [%s]" % ", ".join(self.arg_overlays))

        self.arg_parsed = [] + overlays

        d = YaccDescriptor(overlays[0])
        if not d:
            def reduce_():
                d = defaultdict(dict)
                for section in set(itertools.chain(*map(lambda o: o.keys(), overlays))):
                    for o in overlays:
                        d[section].update(o.get(section, {}))
                return dict(d)
            self.errors = None
            self.params = reduce_()
            return
        self.arg_descriptor = d

        overlays.pop(0)
        resolver.assemble(d, overlays)
        resolver.finalize(d)
        self.errors, self.params = d.collect()

    def validate(self):
        if not self.arg_descriptor and self.arg_validate:
            raise ValueError("No valid descriptor provided.")
        if self.arg_flat and self.arg_format in ('sh', 'make'):
            raise ValueError("Incompatible arguments: flat and this format")
        if self.errors and self.arg_validate:
            d = defaultdict(dict)
            for section, key, err in self.errors:
                d[section][key] = str(err)
            buf = StringIO.StringIO()
            dump(self.errors_to_dict(), buf, default_flow_style=False)
            raise ValueError(buf.getvalue())

    def errors_to_dict(self):
        d = defaultdict(dict)
        for section, key, err in self.errors:
            d[section][key] = str(err)
        return dict(**d)

    def execute(self):
        self.load()
        self.validate()

        # a bit of an edge case, but if you want to run no-validate...
        if self.errors and not self.arg_validate:
            for section, key, _err in self.errors:
                self.params[section] = self.params.get(section, {})
                self.params[section][key] = self.arg_descriptor[section][key].value

        if self.arg_key:
            section, key = self.arg_key.split(".", 1)
            if self.arg_format == 'raw':
                with self.output_stream() as output:
                    output.write("%s\n" % self.params[section][key])
                return
            # else:
            self.params = {section: {key: self.params[section][key]}}

        if self.arg_flat:
            d = {"%s.%s" % (section, key): self.params[section][key] for section in self.params for key in self.params[section]}
            self.params = d

        with self.output_stream() as output:
            f = Formatter(self.params)
            getattr(f, "format_%s" % self.arg_format)(output)

    @contextmanager
    def output_stream(self):
        o = self.arg_output
        buf = StringIO.StringIO()
        try:
            yield buf
        except:
            raise
        if o in ('-', '/dev/stdout') or None:
            sys.stdout.write(buf.getvalue())
            sys.stdout.flush()
            return
        if hasattr(o, 'write') and callable(o.write):
            o.write(buf.getvalue())
            return
        assert isinstance(o, basestring), type(o)
        with safeopen(o) as fd:
            fd.write(buf.getvalue())


class Formatter(object):
    """Dumps configs to specific formats."""

    def __init__(self, params):
        self.params = dict(params)

    def format_raw(self, output):
        output.write("%s\n" % self.params)

    def format_yaml(self, output):
        dump(self.params, output, default_flow_style=False)

    def format_sh(self, output):
        def _norm_sh_key(k):
            return k.upper().replace("-", "_")

        for section in self.params:
            for key, value in self.params[section].iteritems():
                sh_key = "%s__%s" % (_norm_sh_key(section), _norm_sh_key(key))
                if value is None:
                    print >> output, "# %s is unset" % sh_key
                    continue
                print >> output, "read -r -d '' %s<<EOF\n%s\nEOF\nexport %s" % (
                    sh_key, str(value), sh_key)

    def format_pickle(self, output):
        pickle.dump(self.params, output)

    def format_json(self, output):
        json.dump(self.params,
                  output,
                  sort_keys=True,
                  default=repr)

    def format_ini(self, output):
        p = ConfigParser()
        map(p.add_section, self.params.keys())

        def populate(section):
            map(lambda (k, v): p.set(section, k, v), self.params[section].items())

        map(populate, self.params.keys())
        p.write(output)

    def format_make(self, output):
        def _norm_sh_key(k):
            return k.upper().replace("-", "_")

        for section in self.params:
            for key, value in self.params[section].iteritems():
                if value is None:
                    print >> output, "# %s__%s is unset" % (
                        _norm_sh_key(section), _norm_sh_key(key))
                else:
                    print >> output, "define %s__%s\n%s\nendef" % (
                        _norm_sh_key(section), _norm_sh_key(key), str(value))


def main(args=sys.argv[1:]):
    """Console script entry point; ref setup.py"""
    c = Compiler()
    c.argparse(args)
    c.execute()
