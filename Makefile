test:
	pytest

test_nvim:
	VSPEC_VIM=nvim pytest

test_coverage: export PYTEST_ADDOPTS:=--cov pythonx --cov test --cov-report=term-missing:skip-covered
test_coverage: test_nvim

build:
	mkdir $@

build/venv: | build
	python -m venv $@
	# Required on Travis CI.
	$@/bin/python -m ensurepip
	find build/venv -ls

build/venv/bin/vint: | build/venv
	$|/bin/python -m pip install --verbose vim-vint==0.3.19
	find / -name vint -ls

build/venv/bin/flake8: | build/venv
	$|/bin/python -m pip install -q flake8==3.5.0

vint: build/venv/bin/vint
	build/venv/bin/vint after autoload ftplugin plugin

flake8: build/venv/bin/flake8
	build/venv/bin/flake8 pythonx/jedi_*.py

check: vint flake8

clean:
	rm -rf build

.PHONY: test check clean vint flake8
