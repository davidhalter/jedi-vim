''' ------------------------------------------------------------------------
Python initialization
---------------------------------------------------------------------------
here we initialize the jedi stuff '''

import vim

# update the system path, to include the jedi path
import sys
import os

# vim.command('echom expand("<sfile>:p:h:h")') # broken, <sfile> inside function
# sys.path.insert(0, os.path.join(vim.eval('expand("<sfile>:p:h:h")'), 'jedi'))
sys.path.insert(0, os.path.join(vim.eval('expand(s:script_path)'), 'jedi'))

# to display errors correctly
import traceback

# update the sys path to include the jedi_vim script
sys.path.insert(0, vim.eval('expand(s:script_path)'))
try:
    import jedi_vim
except Exception as excinfo:
    raise Exception('Failed to import jedi_vim: {0}\n{1}'.format(
        excinfo, traceback.format_exc()))
finally:
    sys.path.pop(1)
