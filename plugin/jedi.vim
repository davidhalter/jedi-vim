"py_fuzzycomplete.vim - Omni Completion for python in vim
" Maintainer: David Halter <davidhalter88@gmail.com>
" Version: 0.1
"
" This part of the software is just the vim interface. The main source code
" lies in the python files around it.

if !has('python')
    echomsg "Error: Required vim compiled with +python"
    finish
endif

" load plugin only once
if exists("g:loaded_jedi") || &cp
    finish
endif
let g:loaded_jedi = 1

" ------------------------------------------------------------------------
" defaults for jedi-vim
" ------------------------------------------------------------------------
let s:settings = {
    \ 'use_tabs_not_buffers': 1,
    \ 'auto_initialization': 1,
    \ 'goto_command': "'<leader>g'",
    \ 'get_definition_command': "'<leader>d'",
    \ 'related_names_command': "'<leader>n'",
    \ 'rename_command': "'<leader>r'",
    \ 'popup_on_dot': 1,
    \ 'pydoc': "'K'",
    \ 'show_function_definition': 1,
    \ 'function_definition_escape': "'≡'",
    \ 'auto_close_doc': 1
\ }

for [key, val] in items(s:settings)
    if !exists('g:jedi#'.key)
        exe 'let g:jedi#'.key.' = '.val
    endif
endfor


set switchbuf=useopen  " needed for pydoc

if g:jedi#auto_initialization 
    " this is only here because in some cases the VIM library adds their
    " autocompletion as a default, which may cause problems, depending on the
    " order of invocation.
    autocmd FileType python setlocal omnifunc=jedi#complete
endif



python << PYTHONEOF
""" here we initialize the jedi stuff """
import vim

# update the system path, to include the jedi path
import sys
import os
from os.path import dirname, abspath, join
sys.path.insert(0, join(dirname(dirname(abspath(vim.eval('expand("<sfile>")')))), 'jedi'))

# to display errors correctly
import traceback

# update the sys path to include the jedi_vim script
sys.path.append(dirname(abspath(vim.eval('expand("<sfile>")'))))
import jedi_vim
sys.path.pop()

PYTHONEOF

" vim: set et ts=4:
