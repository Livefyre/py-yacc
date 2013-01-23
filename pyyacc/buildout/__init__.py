import logging, os, zc.buildout
from pyyacc.parser import build
from pyyacc.parser import load

def resolve_file(f, buildout):
    if os.path.exists(f):
        return f
    f = os.path.join(buildout['buildout']['directory'], f)
    if os.path.exists(f):
        return f
    raise zc.buildout.UserError('Invalid path: %s' % f)

    
class ParseYAML:
    def __init__(self, buildout, name, options):
        self.name, self.options = name, options
        f = resolve_file(options['file'].strip(), buildout)
        extract = dict(map(lambda x: x.strip().split("."), options['extract'].split("\n")))
        params = load(open(f))
        for section, key in extract.iteritems():
            if section not in params:
                raise zc.buildout.UserError('Invalid section: %s' % section)
            if key not in params[section]:
                raise zc.buildout.UserError('Invalid key: %s.%s' % (section, key))
            
            val = params[section][key]
            if isinstance(val, list):
                val = options.get('list-separator', ",").join(val)
            if isinstance(val, dict):
                for sk in val:
                    options['config-%s-%s' % (section, key)] = str(val[sk])
            else:
                options['config-%s-%s' % (section, key)] = str(val)            

    def install(self):
        return []

    def update(self):
        pass