test:
	py.test

build:
	mkdir $@
build/vint: | build
	python3 -m venv $@
	$@/bin/pip install vim-vint
check: LINT_FILES:=after autoload ftplugin plugin
check: build/vint
	build/vint/bin/vint $(LINT_FILES)

clean:
	rm -rf build

.PHONY: test check clean
