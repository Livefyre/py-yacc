'''
Created on Jan 6, 2013

@author: nino
'''

import sys
from collections import defaultdict
from pyyacc.parser import parse, ConfigurationBuilder, unparse, build
from optparse import OptionParser

def main():
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
    
if __name__ == '__main__': main()