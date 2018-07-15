test:
	pytest test_*.py

build:
	mkdir $@

build/vint: | build
	virtualenv -p python3.6 $@
	$@/bin/pip install vim-vint==0.3.19

build/flake8: | build
	virtualenv -p python3.6 $@
	$@/bin/pip install flake8==3.5.0

vint: build/vint
	build/vint/bin/vint after autoload ftplugin plugin

flake8: build/flake8
	build/flake8/bin/flake8 pythonx/jedi_*.py

check: vint flake8

clean:
	rm -rf build

.PHONY: test check clean vint flake8
