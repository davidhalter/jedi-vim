test:
	py.test

build:
	mkdir $@
build/vint: | build
	virtualenv -p python3.6 $@
	$@/bin/pip install vim-vint==0.3.19
check: LINT_FILES:=after autoload ftplugin plugin
check: build/vint
	build/vint/bin/vint $(LINT_FILES)

clean:
	rm -rf build

.PHONY: test check clean
