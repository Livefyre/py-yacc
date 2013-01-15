import os
from setuptools import setup

from pyyacc import __version__

setup(
    name = "py-yacc",
    version = __version__,
    author = "Nino Walker",
    author_email = "nino.walker@gmail.com",
    description = ("A YAML based configuration DSL and associated parser/validator."),
    url="https://github.com/Livefyre/py-yacc",
    license = "BSD",
    packages=['pyyacc'],
    long_description=open('README.md').read(),
    install_requires=['PyYAML>=3.10',],
    setup_requires=['nose>=1.0', 'coverage', 'nosexcover'],
    test_suite = 'nose.collector',
    classifiers=[
        "License :: OSI Approved :: BSD License",
    ],
    entry_points={
      'console_scripts': ['pyyacc.validate = pyyacc.scripts.compile:main']
    }
)
