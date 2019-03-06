.PHONY: test

coverage: test
	open cover/index.html

test: env
	env/bin/nosetests --with-xcover --cover-html

pypi.upload:
	python setup.py sdist upload -r https://upload.pypi.org/legacy/

env: env/bin/activate
env/bin/activate: setup.py requirements.txt
	test -f $@ || virtualenv --no-site-packages env
	env/bin/pip install -e . -e .[test] -r requirements.txt
	touch $@

lint: | env/bin/activate
	yapf -i --recursive --style='{based_on_style: chromium, indent_width: 4, column_limit: 120}' \
		pyyacc pyyacc3 test
