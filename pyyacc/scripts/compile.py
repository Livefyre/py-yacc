'''
Created on Jan 6, 2013

@author: nino
'''

import sys
from collections import defaultdict, OrderedDict
from pyyacc.parser import parse, unparse, build
from optparse import OptionParser
import os
import pickle
import json
from pyyacc.objects import ParseResult


def validate_main():
    usage = "usage: %prog [options] yaml [yaml ...]"
    parser = OptionParser(usage=usage)
    parser.add_option("-i", "--ignore_requirements", dest="ignored",
                      default=None,
                      help="requirements to ignore for validation purposes.")
    parser.add_option("-f", "--format", dest="format",
                      default="yaml",
                      help="Output format: yaml, json, sh, make are supported.")

    (options, yamls) = parser.parse_args()
    if not yamls:
        parser.print_usage()
        exit(-1)
    b, params = build(*yamls)
    errs = b.validate(params, ignored=options.ignored.split(",") if options.ignored else [])
    if errs:
        d = defaultdict(dict)
        for (section, key), err in errs.iteritems():
            d[section][key] = str(err)
        unparse(sys.stderr, dict(d), default_flow_style=False)
        sys.exit(1)
        return

    if options.format == 'yaml':
        unparse(sys.stdout, dict(params.iteritems()), default_flow_style=False)
    elif options.format == 'pickle':
        pickle.dump(dict(params), sys.stdout)
    elif options.format == 'json':
        json.dump(dict(params),
                  sys.stdout,
                  sort_keys=True,
                  indent=2,
                  separators=(',', ': '))
    elif options.format == 'sh':
        for section in params:
            for key, value in params[section].iteritems():
                if value is None:
                    print "# %s__%s is unset" % (_norm_sh_key(section), _norm_sh_key(key))
                else:
                    print "read -r -d '' %s__%s<<EOF\n%s\nEOF\n" % (_norm_sh_key(section), _norm_sh_key(key), str(value))
                    print "export %s__%s\n" % (_norm_sh_key(section), _norm_sh_key(key))
    elif options.format == 'make':
        for section in params:
            for key, value in params[section].iteritems():
                if value is None:
                    print "# %s__%s is unset" % (_norm_sh_key(section), _norm_sh_key(key))
                else:
                    print "%s__%s=%s" % (_norm_sh_key(section), _norm_sh_key(key), str(value))
    else:
        print >> sys.stderr, "Invalid output format."
        sys.exit(2)
    sys.exit(0)

def _norm_sh_key(k):
    return k.upper().replace("-", "_")

def sources_main():
    usage = "usage: %prog [options] yaml [yaml ...]"
    parser = OptionParser(usage=usage)
    #parser.add_option("-L", "--output-layers", dest="layers", action="store_true",
    #                  default=False,
    #                  help="Display where values are sourced from.")

    (options, yamls) = parser.parse_args()
    if not yamls:
        parser.print_usage()
        exit(-1)
    descriptor = parse(open(yamls[0]))
    parsed = [parse(open(f)) for f in yamls[1:]]
    params = OrderedDict()
    for section in descriptor.keys():
        params[section] = {}
        for key in descriptor[section]:
            for yam, yam_d in zip(yamls, [descriptor] + parsed):
                if key in yam_d.get(section, {}):
                    params[section][key] = os.path.basename(yam)
    unparse(sys.stdout, dict(params), default_flow_style=False)

