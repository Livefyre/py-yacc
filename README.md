
# pyyacc

Python implementation of a Yet Another Configuration Compiler.

## Why? What about INI, XML, JSON, or plain Python?

The YACC DSL provides an efficient way to specify, document, and construct
a typed configuration system that supports common patterns through overlays,
environment injection, default, optional, and required variables.

None of the above support this as simply or clearly as the YACC DSL and
python configuration builder.

## Concepts

The system is built around three concepts:

* A YACC Descriptor, authored in a YAML DSL.
* Overlays which are additive.
* Output, which represents the assembly of a YACC Descriptor and the Overlays.

### YACC Descriptor

The YACC Descriptor borrows heavily from the INI format: a configuration is a
collection of `sections`, with one or more `keys` within a section.

The YACC Descriptor adds the notion of a `Specification`, which describes a `key`:

* The type
* A default value (or `optional` or `required`)
* Documenation
* Examples
* Deprecated (flag)
* Sensitive

#### Example

```yaml
webserver:
  port: !spec
    description: Port to accept general traffic.
    type: !!int "0"
    value: 80
  debug: !spec
    description: Is debug mode enabled.
    type: !!bool "0"
    value: false
  public-name: !spec
    description: DNS name for routing public traffic (e.g. redirects).
    type: !!str ""
    value: !environment HOSTNAME
  ssl-private-key: !spec
    description:
    sensitive: true
    type: !!str ""
    value: !required        
```

### Overlays

An overlay is simply a set of key-level overrides, where last takes precedence.

#### Overlay as JSON

This can be provided as a YAML document (or equivalent JSON):

```yaml
webserver:
  port: 9999
```

#### Overlay as ENV variable

Via a key the environment (the prefix is configurable):

```sh
export YACC__WEBSERVER__PORT=9999
```

### Output

After merging the descriptor and all overlays via the algorithm described below
the compiled configuration is a `Dict[section, Dict[key, value]]`

This can be injected into a running python process or output via the CLL into formats
consumable by other programs (INI, SH, Make, JSON).


## Resolution Algorithm

### Overlay Assembly

```python
desc_object = yml.load(open(file).read()) #: :type: Dict[str, Dict[str, ValueSpec]]

resolver = YaccResolver(desc_object)
resolver.assemble(overlays)
```

#### 1. Parse the descriptor and provided overlays.

The descriptor defines the complete set of accepted parameters as defined by `ValueSpec` objects.

#### 2. Resolve overlays as defined in the environment

```python
default_overlays = [EnvVar("YACC__OVERLAY")]
extra_overlays = os.environ.get("PYACC_RESOLVER__OVERLAYS")
if not extra_overlays:
    extra_overlays = default_overlays
return map(yml.load, filter(None, map(read, extra_overlays)))    
```

#### 3. Define the environment key prefix `${ENV_PREFIX}`

The environment prefix is used to resolve key-specific overlays.

```python
env_prefix = os.environ.get("YACC_RESOLVER__ENV_PREFIX", "PYYACC")
```


#### 4. Construct an overlay from the environment

- Values are parsed as YAML values.
- Section/keys map to:

```python
re.sub(r'[^a-z0-9]', '_', "%s__%s__%s" % (env_prefix, section, key), flags=re.I).upper()
```

####  4. Merge down each overlay onto the descriptor.

```python
descriptor.update(*itertools.chain(provided_overlays, extra_overlays, [environment_overlay]))
```

### Final Resolution

```python
descriptor.finalize()
```

#### 1. Iterate over all ValueSpecs

1. Resolve any values !environment objects.
2. Validate type against the spec.
3. Store values and errors.

## CLI


```bash
pyyacc3 -h
```

    Usage: pyyacc3 [options] yaml [yaml ...]

    Options:
      -h, --help            show this help message and exit
      -v                    Verbose logging output.
      -V                    Very verbose logging output.
      --flat                Flatten into 'section.key': value notation
      -f ARG_FORMAT, --format=ARG_FORMAT
                            Output format: yaml, json, sh, make are supported.
      --no-validate         Disable validation [default: on]
      -o ARG_OUTPUT, --output=ARG_OUTPUT
                            Output destination: path where to write output. If not
                            provided, stdout is used.
      --env-prefix=ARG_ENV_PREFIX
                            Prefix for overlays from the environment
      --env-overlay=ARG_ENV_OVERLAY
                            Name of an overlay to load from the environment


# Release

```bash
make pypi.upload
```
