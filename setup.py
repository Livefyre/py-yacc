from setuptools import setup, find_packages

from pyyacc3 import __version__

tests_require = ['tox', 'pytest', 'pytest-cov', 'mock', 'nose>=1.0', 'coverage', 'coverage_pth', 'nosexcover']

setup(
    name="py-yacc",
    version=__version__,
    author="Nino Walker",
    author_email="nino.walker@gmail.com",
    description=("A YAML based configuration DSL and associated parser/validator."),
    url="https://github.com/Livefyre/py-yacc",
    license="BSD",
    packages=find_packages(exclude=('test',)),
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    install_requires=['PyYAML>=3.12', 'safeoutput'],
    classifiers=[
        "License :: OSI Approved :: BSD License",
        'Development Status :: 5 - Production/Stable',
        'Topic :: Software Development :: Libraries',
        'Topic :: System :: Filesystems',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.5',
    ],
    tests_require=tests_require,
    extras_require={'test': tests_require},
    entry_points={
        'console_scripts': ['pyyacc.validate = pyyacc.scripts.compile:validate_main',  # deprecated
                            'pyyacc = pyyacc.scripts.compile:validate_main',
                            'pyyacc3 = pyyacc3.compile:main']
    },
    zip_safe=True,
)
