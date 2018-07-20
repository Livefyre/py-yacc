import StringIO
import os
from unittest import TestCase

from mock import patch

from pyyacc3.compile import Compiler, Formatter, main
from pyyacc3.descriptor import YaccDescriptor
from pyyacc3.yml.extensions import Requirement, ValueSpec


SPEC_YAML_PATH = os.path.join(os.path.dirname(__file__), "spec.yaml")


class TestCLI(TestCase):
    def argparse(self, cl, **kwargs):
        c = Compiler()
        c.argparse(cl.split(" "))
        print c.__dict__
        self.assertValues(c, **kwargs)
        return c

    def assertValues(self, c, **kwargs):
        for k, v in kwargs.items():
            cval = getattr(c, k)
            self.assertEquals(v, cval, "%s: %s != %s" % (k, v, cval))

    def test_basic_parse(self):
        self.argparse("--flat meow.yaml", arg_flat=True, arg_overlays=["meow.yaml"])

    def test_flags(self):
        self.argparse("--flat meow.yaml", arg_flat=True, arg_validate=True)
        self.argparse("--no-validate meow.yaml", arg_validate=False)

    def test_formats(self):
        self.argparse("", arg_format="yaml")
        self.argparse("--format=sh", arg_format="sh")
        self.argparse("--format sh", arg_format="sh")
        self.assertRaises(SystemExit, self.argparse, "-f xxx")
        self.argparse("-f sh -o output cluster.yaml", arg_format="sh",
                      arg_output="output", arg_overlays=["cluster.yaml"])

    def test_overlays(self):
        self.argparse("", arg_format="yaml")
        self.argparse("--format=sh meow.yaml moo.yaml", arg_format="sh",
                      arg_overlays=["meow.yaml", "moo.yaml"])

    def test_validates(self):
        c = self.argparse("--no-validate --flat meow.yaml")
        c.validate()

    def test_validate_fails(self):
        c = self.argparse("")
        c.arg_overlays = []
        self.assertRaises(ValueError, c.validate)

        c = self.argparse("--flat -f sh meow.yaml", arg_format="sh")
        c.arg_descriptor = YaccDescriptor(dict(meow=dict(moo=ValueSpec(str, Requirement("meow")))))
        self.assertRaises(ValueError, c.validate)

        c = self.argparse("")
        c.arg_descriptor = YaccDescriptor(dict(meow=dict(moo=ValueSpec(str, Requirement("meow")))))
        c.errors = [('meow', 'moo', 'err')]
        self.assertRaises(ValueError, c.validate)
        try:
            c.validate()
            assert False
        except ValueError, e:
            self.assertEquals(str(e), "meow:\n  moo: err\n")

    def test_load(self):
        c = Compiler()
        c.init(overlays=[SPEC_YAML_PATH])
        c.load()
        self.assertEquals(3, len(c.errors))
        self.assertEquals(100.1, c.params['tests']['float'])

    @patch('pyyacc3.compile.sys.stdout.write')
    def test_outputstream_stdout(self, write):
        c = Compiler()
        c.init(output="-")
        with c.output_stream() as o:
            o.write("1")
        write.assert_called_once_with("1")

    @patch('pyyacc3.compile.sys.stdout.write')
    def test_outputstream_stdout_no_ouptut(self, write):
        c = Compiler()
        c.init(output="-")
        try:
            with c.output_stream():
                raise ValueError
        except ValueError:
            pass
        write.assert_not_called()

    def test_outputstream_to_file(self):
        c = Compiler()
        fn = "meow.yaml"
        c.init(output=fn)
        self.addCleanup(os.unlink, fn)
        self.assertFalse(os.path.exists(fn))
        with c.output_stream() as out:
            Formatter({"meow": True}).format_yaml(out)
            self.assertFalse(os.path.exists(fn))  # data is only flushed at close
        self.assertTrue(os.path.exists(fn))


class TestMain(TestCase):
    def test_main_okay(self):
        fn = "moo.yaml"
        self.addCleanup(os.unlink, fn)
        self.assertFalse(os.path.exists(fn))
        main(("-f yaml -o %s --no-validate %s" % (fn, SPEC_YAML_PATH)).split(" "))
        self.assertTrue(os.path.exists(fn))

    def test_main_validate_fails(self):
        fn = "moo.yaml"
        self.assertFalse(os.path.exists(fn))
        with self.assertRaises(ValueError):
            main(("-f yaml -o %s %s" % (fn, SPEC_YAML_PATH)).split(" "))
        self.assertFalse(os.path.exists(fn))


class TestFormatter(TestCase):
    maxDiff = None

    def execute(self, format_, expected):
        c = Compiler()
        buf = StringIO.StringIO()
        c.init(overlays=[os.path.join(os.path.dirname(__file__), "spec.yaml")],
               validate=False,
               format=format_,
               output=buf)
        c.execute()
        try:
            self.assertEquals(expected, buf.getvalue())
        except:
            with open(format_, "w") as o:
                o.write(buf.getvalue())
            print "Failure; output rendered to: %s" % format_
            raise

    def test_format_yaml(self):
        self.execute("yaml", YAML_OUTPUT)

    def test_sh(self):
        self.execute("sh", SH_OUTPUT)

    def test_format_ini(self):
        self.execute("ini", INI_OUTPUT)

    def test_format_make(self):
        self.execute("make", MAKE_OUTPUT)


YAML_OUTPUT = """email:
  backend: !required "Requirement(must be set in the environment.yaml)"
  cruft: Iamdead
  from_address: notify@example.com
misconfiguration_examples:
  invalid_value: I am a string.
mqueue:
  redis_host: !required "Requirement(from cluster)"
tests:
  bool: false
  float: 100.1
  int: 1
  list:
  - 1
  optlist: null
uris:
  mongo: !uri "mongodb://db1.example.net,db2.example.net:2500/?replicaSet=test"
  mongo-sock: !uri "mongodb:///tmp/mongodb-27017.sock"
  smtp: !uri "smtp://example.com:25/"
  www: !uri "http://www.google.com"
"""

SH_OUTPUT = """read -r -d '' MISCONFIGURATION_EXAMPLES__INVALID_VALUE<<EOF
I am a string.
EOF
export MISCONFIGURATION_EXAMPLES__INVALID_VALUE
read -r -d '' TESTS__INT<<EOF
1
EOF
export TESTS__INT
read -r -d '' TESTS__BOOL<<EOF
False
EOF
export TESTS__BOOL
read -r -d '' TESTS__FLOAT<<EOF
100.1
EOF
export TESTS__FLOAT
read -r -d '' TESTS__LIST<<EOF
[1]
EOF
export TESTS__LIST
# TESTS__OPTLIST is unset
read -r -d '' MQUEUE__REDIS_HOST<<EOF
Requirement(from cluster)
EOF
export MQUEUE__REDIS_HOST
read -r -d '' EMAIL__BACKEND<<EOF
Requirement(must be set in the environment.yaml)
EOF
export EMAIL__BACKEND
read -r -d '' EMAIL__FROM_ADDRESS<<EOF
notify@example.com
EOF
export EMAIL__FROM_ADDRESS
read -r -d '' EMAIL__CRUFT<<EOF
Iamdead
EOF
export EMAIL__CRUFT
read -r -d '' URIS__WWW<<EOF
http://www.google.com
EOF
export URIS__WWW
read -r -d '' URIS__SMTP<<EOF
smtp://example.com:25/
EOF
export URIS__SMTP
read -r -d '' URIS__MONGO<<EOF
mongodb://db1.example.net,db2.example.net:2500/?replicaSet=test
EOF
export URIS__MONGO
read -r -d '' URIS__MONGO_SOCK<<EOF
mongodb:///tmp/mongodb-27017.sock
EOF
export URIS__MONGO_SOCK
"""

INI_OUTPUT = """[misconfiguration_examples]
invalid_value = I am a string.

[tests]
int = 1
bool = False
float = 100.1
list = [1]
optlist = None

[mqueue]
redis_host = Requirement(from cluster)

[email]
backend = Requirement(must be set in the environment.yaml)
from_address = notify@example.com
cruft = Iamdead

[uris]
www = http://www.google.com
smtp = smtp://example.com:25/
mongo = mongodb://db1.example.net,db2.example.net:2500/?replicaSet=test
mongo-sock = mongodb:///tmp/mongodb-27017.sock

"""

MAKE_OUTPUT = """define MISCONFIGURATION_EXAMPLES__INVALID_VALUE
I am a string.
endef
define TESTS__INT
1
endef
define TESTS__BOOL
False
endef
define TESTS__FLOAT
100.1
endef
define TESTS__LIST
[1]
endef
# TESTS__OPTLIST is unset
define MQUEUE__REDIS_HOST
Requirement(from cluster)
endef
define EMAIL__BACKEND
Requirement(must be set in the environment.yaml)
endef
define EMAIL__FROM_ADDRESS
notify@example.com
endef
define EMAIL__CRUFT
Iamdead
endef
define URIS__WWW
http://www.google.com
endef
define URIS__SMTP
smtp://example.com:25/
endef
define URIS__MONGO
mongodb://db1.example.net,db2.example.net:2500/?replicaSet=test
endef
define URIS__MONGO_SOCK
mongodb:///tmp/mongodb-27017.sock
endef
"""
