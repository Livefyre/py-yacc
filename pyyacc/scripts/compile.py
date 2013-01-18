'''
Created on Jan 6, 2013

@author: nino
'''

import sys
from collections import defaultdict, OrderedDict
from pyyacc.parser import parse, ConfigurationBuilder, unparse, build
from optparse import OptionParser
import os

def validate_main():
    usage = "usage: %prog [options] yaml [yaml ...]"
    parser = OptionParser(usage=usage)
    parser.add_option("-i", "--ignore_requirements", dest="ignored",
                      default=None,
                      help="requirements to ignore for validation purposes.")

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
    
    unparse(sys.stdout, dict(params.iteritems()), default_flow_style=False)
    sys.exit(0)

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
    
