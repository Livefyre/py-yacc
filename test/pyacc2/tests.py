import unittest
import os
from pyyacc.parser import ConfigBuilder
from nose.tools import assert_raises  # @UnresolvedImport
import StringIO
from pyyacc.yml.extensions import Requirement
from pyyacc.cfgparse import ConfigParserAdaptor


def fd(yamlstr):
    return StringIO.StringIO(yamlstr)


class BaseTest(unittest.TestCase):
    def open(self, filename):
        f = os.path.join(os.path.dirname(__file__), filename)
        return open(f)

    def fd(self, string):
        return StringIO.StringIO(string)


class TestBuilder(BaseTest):

    def test_build_1(self):
        spec1 = fd("""
    section:
      param: !spec
        type: !!int "0"
        description:
        value: 1
        deprecated: true
        """)
        _builder, params = ConfigBuilder.parse(spec1)
        assert isinstance(params, dict)
        assert params['section']['param'] == 1

    def test_build_2(self):
        spec1 = fd("""
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
        _builder, params = ConfigBuilder.parse(spec1)
        assert params['section']['param'] == 1
        assert params['section2']['param'] == 1

    def test_overlay_1(self):
        spec1 = fd("""
    section:
      param: !spec
        type: !!int "0"
        description:
        value: 1
      param2: !spec
        type: !!int "0"
        description:
        value: !optional
        """)
        over = fd("""
    section:
      param: 2
        """)
        _builder, params = ConfigBuilder.parse(spec1, over)
        assert params['section']['param'] == 2
        assert 'param2' not in params['section']

    def test_overlay_2(self):
        spec1 = fd("""
    section:
      param: !spec
        type: !!int "0"
        description:
        value: 1
        """)
        over = fd("""
    section:
      param: 2
        """)
        over2 = fd("""
    section:
      param: 3
        """)
        _builder, params = ConfigBuilder.parse(spec1, over, over2)
        assert params['section']['param'] == 3

    def test_validator_no_errors(self):
        spec1 = fd("""
    section:
      param: !spec
        type: !!int "0"
        description:
        value: !required
        """)
        over = fd("""
    section:
      param: 2
        """)
        _builder, params = ConfigBuilder.parse(spec1, over)
        assert params['section']['param'] == 2

        errors = _builder.validate(params)
        assert not errors

    def test_validator_required(self):
        spec1 = fd("""
    section:
      param: !spec
        type: !!int "0"
        description:
        value: !required
        """)
        over = fd("""
    section:
      param2: 2
        """)
        _builder, params = ConfigBuilder.parse(spec1, over)
        errors = _builder.validate(params)
        assert ('section', 'param') in errors
        assert isinstance(errors[('section', 'param')], Requirement)

    def test_empty_fle(self):
        spec1 = fd("""
    section:
      param: !spec
        type: !!int "0"
        description:
        value: !required
        """)
        over = fd("""
        """)
        _builder, params = ConfigBuilder.parse(spec1, over)
        errors = _builder.validate(params)
        # should be normal errors
        assert ('section', 'param') in errors
        assert isinstance(errors[('section', 'param')], Requirement)

    def test_validator_type_error(self):
        spec1 = fd("""
    section:
      param: !spec
        type: !!int "0"
        description:
        value: !required
        """)
        over = fd("""
    section:
      param: foo
        """)
        _builder, params = ConfigBuilder.parse(spec1, over)
        assert params['section']['param'] == 'foo'
        errors = _builder.validate(params)
        assert errors
        assert ('section', 'param') in errors
        assert isinstance(errors[('section', 'param')], TypeError)

    def test_validator_type_list(self):
        spec1 = fd("""
    section:
      param: !spec
        type: [ !!int "0", !!null ]
        description:
        value: !required
        """)
        over = fd("""
    section:
      param: !!null
        """)
        _builder, params = ConfigBuilder.parse(spec1, over)
        assert params['section']['param'] == None

        errors = _builder.validate(params)
        assert not errors


class TestConfigParserFacade(BaseTest):
    def test1(self):
        builder, params = ConfigBuilder.parse(os.path.join(os.path.dirname(__file__), "spec.yaml"))
        v = builder.descriptor
        f = ConfigParserAdaptor(params)

        def compare(method, section, key, type_):
            assert f.has_section(section)
            assert f.has_option(section, key)
            assert key in f.options(section)
            assert key in dict(f.items(section))
            self.assertEqual(method(section, key), params[section][key])
            assert isinstance(method(section, key), type_)

        compare(f.get, "email", "from_address", basestring)
        compare(f.getint, "tests", "int", int)
        compare(f.getboolean, "tests", "bool", bool)
        compare(f.getfloat, "tests", "float", float)
        compare(f.getlist, "tests", "list", list)

        assert f.getlist('tests', 'list') == [1]
        assert v['tests']['list'].obj_type == list
        assert v['tests']['optlist'].obj_type == (list, type(None))
        assert v['tests']['optlist'].value == None
