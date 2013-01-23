py-yacc
=======

Python implementation of a Yet Another Configuration Compiler.

Why? What about INI, XML, JSON, or plain Python?
------------------------------------------------

Except for XML and Python, the other options offer limited typing options. 
XML is cumbersome. Plain Python is not platform independent.

Also, none of these provide solutions for defining configuration requirements.
Not options, requirements: things that must be provided inorder to have a 
functional environment. E.g. external resources - databases, hostnames, etc.
that form the backbone of a modern cloud application.
 
Enter the YACC DSL.

The YACC DSL
------------

At the base is a configuration descriptor. This is a plain old YAML map document with a few additions:

- `!spec`: used to describe a setting value. It must have `description`, `type`, and `value`.
- `!required`: used as a `value` to identify something that MUST BE provided externally,
   and validation of compiled parameters WILL fail.
- `!optional`: used to identify settings that may not be set at all. If not provided externally,
   a compiled configuration will not contain this setting.
- `!uri`: a resource path that can be parsed as a URI. E.g. mongodb://host/db/collection


Example
-------

    i_am_a_section:
      i_am_a_default_setting: !spec
        description: What I am used for
        type: !!str ""
        value: setting_value
      i_am_a_required_setting: !spec
        description: I am required by the application, and 
          I cannot have a default.
        type: !!str ""
        value: !required "where should I be set."
    i_am_another_section:
      i_am_a_map: !spec
        description: What I am used for
        type: {}
        value:
          some: thing
          more: than
          a: scalar
      i_am_a_list: !spec
        description: What I am used for
        type: []
        value: [ a, b, c]
      i_am_a_uri: !spec
        description: What I am used for
        type: !uri
        value: !uri "http://www.google.com"
        

Using with buildout
-------------------

    [read-params]
    recipe = py-yacc:parse
    file = i_am_a_yaml.yaml
    extract = i_am_a_section.i_am_a_setting
      i_am_a_section.i_am_a_list
    # list-separator = , - default
    
    [inject-params]
    recipe = collective.recipe.template
    output = to_a_file
    input = inline:
      Use me: ${read-params:config-i_am_a_section-i_am_a_setting}
      Use me too: ${read-params:config-i_am_a_section-i_am_a_list}
