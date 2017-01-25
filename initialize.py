"""Python initialization for jedi module."""

try:
    import traceback
except Exception as excinfo:
    raise Exception('Failed to import traceback: {0}'.format(excinfo))

try:
    import os, sys, vim
    jedi_path = os.path.join(vim.eval('expand(s:script_path)'), 'jedi')
    sys.path.insert(0, jedi_path)

    jedi_vim_path = vim.eval('expand(s:script_path)')
    if jedi_vim_path not in sys.path:  # Might happen when reloading.
        sys.path.insert(0, jedi_vim_path)
except Exception as excinfo:
    raise Exception('Failed to add to sys.path: {0}\n{1}'.format(
        excinfo, traceback.format_exc()))

try:
    import jedi_vim
except Exception as excinfo:
    raise Exception('Failed to import jedi_vim: {0}\n{1}'.format(
        excinfo, traceback.format_exc()))
finally:
    sys.path.remove(jedi_path)
