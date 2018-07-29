test:
	pytest

build:
	mkdir $@

build/venv: | build
	virtualenv -p python3.6 $@

build/venv/bin/vint: | build/venv
	$|/bin/pip install vim-vint==0.3.19

build/venv/bin/flake8: | build/venv
	$|/bin/pip install flake8==3.5.0

vint: build/venv/bin/vint
	build/venv/bin/vint after autoload ftplugin plugin

flake8: build/venv/bin/flake8
	build/venv/bin/flake8 pythonx/jedi_*.py

check: vint flake8

clean:
	rm -rf build

.PHONY: test check clean vint flake8
