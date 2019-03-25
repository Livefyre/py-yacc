.PHONY: test clean pypi.upload

coverage: test
	open cover/index.html

test: env
	YACC__OVERLAY= YACC_RESOLVER__OVERLAYS= env/bin/nosetests --with-xcover --cover-html

pypi.upload:
	python setup.py sdist upload -r https://upload.pypi.org/legacy/

env: env/bin/activate
env/bin/activate: setup.py requirements.txt
	test -f $@ || virtualenv -p python3 --no-site-packages env
	env/bin/pip3 install -e . -e .[test] -e .[dev]
	touch $@


lint:
	env/bin/isort -q --recursive test pyyacc3
	env/bin/yapf -i --recursive test pyyacc3

clean:
	rm -rf cover env
