import io
import unittest

from pyyacc3.yml import load
from pyyacc3.yml.extensions import Requirement, URI, ValueSpec, Optional


parse = load


class TestRegistration(unittest.TestCase):
    def test_required(self):
        load("!required cluster.yaml")


class TestParser(unittest.TestCase):
    def fd(self, string):
        return io.StringIO(string)

    def test_parse_requirement(self):
        x = parse(self.fd("""!required "abc" """))
        assert isinstance(x, Requirement)
        repr(x)

    def test_parse_optional(self):
        x = parse(self.fd("""!optional "abc" """))
        assert isinstance(x, Optional)
        repr(x)

    def test_parse_uri(self):
        x = parse(self.fd("""!uri "smtp://host:25/" """))
        assert isinstance(x, URI), type(x)
        assert str(x) == "smtp://host:25/"
        x = x.parse()
        assert x.hostname == "host"
        assert x.port == 25
        assert x.scheme == "smtp"

    def test_parse_spec(self):
        x = parse(self.fd("""!spec\ntype: !!int "0"\ndescription:\nvalue: 1"""))
        assert isinstance(x, ValueSpec)
        assert x.expected_type == int
        assert x.value == 1
        assert not x.description
        assert not x.examples
        assert not x.deprecated

        x = parse(self.fd("""!spec\ntype: !!int "0"\ndescription:\nvalue: 1\ndeprecated: true"""))
        assert x.deprecated
        repr(x)
