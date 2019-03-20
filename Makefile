.PHONY: test

PY_SRC = $(shell git ls-files | grep '.py')

coverage: test
	open cover/index.html

test: # env
	tox
	# env/bin/nosetests --with-xcover --cover-html

pypi.upload:
	python setup.py sdist upload -r https://upload.pypi.org/legacy/

env: env/bin/activate
env/bin/activate: setup.py requirements.txt
	test -f $@ || virtualenv --no-site-packages env
	env/bin/pip install -e . -e .[test] -r requirements.txt
	touch $@


lint: $(PY_SRC)
	isort $(PY_SRC)
	yapf -i $(PY_SRC)