import StringIO
import os
import unittest

from pyyacc3.cfgparse import ConfigParserAdaptor
from pyyacc3.compile import Compiler
from pyyacc3.yml.extensions import Requirement, ConfigError


def fd(yamlstr):
    return StringIO.StringIO(yamlstr)


class BaseTest(unittest.TestCase):
    def open(self, filename):
        f = os.path.join(os.path.dirname(__file__), filename)
        return open(f)

    def fd(self, string):
        return StringIO.StringIO(string)


class TestBuilder(BaseTest):

    def load(self, contents, *overlays):
        spec1 = fd(contents)
        comp = Compiler().init(overlays=[spec1] + map(fd, overlays))
        comp.load()
        return comp, comp.params, comp.errors

    def test_build_1(self):
        comp, params, errors = self.load("""
    section:
      param: !spec
        type: !!int "0"
        description:
        value: 1
        deprecated: true
        """)
        assert isinstance(params, dict)
        assert params['section']['param'] == 1

    def test_build_2(self):
        comp, params, errors = self.load("""
    section:
      param: !spec
        type: !!int "0"
        description:
        value: 1

    section2:
      param: !spec
        type: !!int "0"
        description:
        value: 1
        """)
        assert params['section']['param'] == 1
        assert params['section2']['param'] == 1

    def test_overlay_1(self):
        comp, params, errors = self.load("""
    section:
      param: !spec
        type: !!int "0"
        description:
        value: 1
      param2: !spec
        type: !!int "0"
        description:
        value: !optional
        """,
        """
    section:
      param: 2
        """)
        self.assertEquals(params, dict(section=dict(param=2)))

    def test_overlay_2(self):
        comp, params, errors = self.load("""
    section:
      param: !spec
        type: !!int "0"
        description:
        value: 1
        """,
        """
    section:
      param: 2
        """,
        """
    section:
      param: 3
        """)
        params = comp.params
        assert params['section']['param'] == 3

    def test_validator_no_errors(self):
        comp, params, errors = self.load("""
    section:
      param: !spec
        type: !!int "0"
        description:
        value: !required
        ""","""
    section:
      param: 2
        """)
        params = comp.params
        assert params['section']['param'] == 2

        errors = comp.errors
        assert not errors

    def test_validator_required(self):
        comp, params, errors = self.load("""
    section:
      param: !spec
        type: !!int "0"
        description:
        value: !required
        ""","""
    section:
      param2: 2
        """)
        assert ('section', 'param', Requirement("")) in errors

    def test_empty_fle(self):
        comp, params, errors = self.load("""
    section:
      param: !spec
        type: !!int "0"
        description:
        value: !required "meow"
        """,
        """
        """)
        # should be normal errors
        assert ('section', 'param', Requirement("meow")) in errors

    def test_validator_type_error(self):
        comp, params, errors = self.load("""
    section:
      param: !spec
        type: !!int "0"
        description:
        value: !required "meow"
        """,
        """
    section:
      param: foo
        """)
        self.assertEqual(params, {})
        assert errors
        assert ('section', 'param') == errors[0][0:2]
        assert isinstance(errors[0][2], ConfigError)

    def test_validator_type_list(self):
        _comp, params, errors = self.load("""
    section:
      param: !spec
        type: [ !!int "0", !!null ]
        description:
        value: !required
        """,
        """
    section:
      param: !!null
        """)
        assert params['section']['param'] == None
        assert not errors


class TestConfigParserFacade(BaseTest):
    def test1(self):
        key = "yacc__misconfiguration_examples__invalid_value".upper()
        os.environ[key] = "101"
        self.addCleanup(lambda: os.unsetenv(key))
        comp = Compiler().init(overlays=[os.path.join(os.path.dirname(__file__), "spec.yaml")])
        comp.load()
        v = comp.arg_descriptor
        self.assertTrue(bool(comp.params))
        params = comp.params
        f = ConfigParserAdaptor(comp.params)

        def compare(method, section, key, type_):
            assert f.has_section(section)
            assert f.has_option(section, key)
            assert key in f.options(section)
            assert key in dict(f.items(section))
            self.assertEqual(method(section, key), params[section][key])
            assert isinstance(method(section, key), type_)

        compare(f.get, "email", "from_address", basestring)
        compare(f.getint, "tests", "int", int)
        compare(f.getint, "misconfiguration_examples", "invalid_value", int)
        compare(f.getboolean, "tests", "bool", bool)
        compare(f.getfloat, "tests", "float", float)
        compare(f.getlist, "tests", "list", list)

        assert f.getlist('tests', 'list') == [1]
        assert v['tests']['list'].expected_type == list
        assert v['tests']['optlist'].expected_type == (list, type(None))
        assert v['tests']['optlist'].value == None
