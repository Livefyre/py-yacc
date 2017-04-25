.PHONY: test

coverage: test
	open cover/index.html

test: env
	env/bin/nosetests --with-xcover --cover-html

pypi.upload:
	python setup.py sdist upload -r https://upload.pypi.org/legacy/

env: env/bin/activate
env/bin/activate: setup.py
	test -f $@ || virtualenv --no-site-packages env
	env/bin/pip install -e .
	env/bin/pip install -e .[test]
	touch $@
