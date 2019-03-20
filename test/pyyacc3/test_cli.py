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
    maxDiff = 100

    def execute(self, format_):
        fname = os.path.dirname(__file__) + "/expected-output-" + format_
        err_fname = fname + ".err"
        c = Compiler()
        buf = StringIO.StringIO()
        c.init(overlays=[os.path.join(os.path.dirname(__file__), "spec.yaml")],
               validate=False,
               format=format_,
               output=buf)
        c.execute()
        try:
            self.assertEquals(open(fname).read(), buf.getvalue())
        except:
            with open(err_fname, "w") as o:
                o.write(buf.getvalue())
            print "Failure; output rendered to: %s" % err_fname
            raise

    def test_format_yaml(self):
        self.execute("yaml")

    def test_sh(self):
        self.execute("sh")

    def test_format_ini(self):
        self.execute("ini")

    def test_format_make(self):
        self.execute("make")

