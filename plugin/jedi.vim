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
if !exists("g:jedi#use_tabs_not_buffers ")
    let g:jedi#use_tabs_not_buffers = 1
endif
if !exists("g:jedi#auto_initialization")
    let g:jedi#auto_initialization = 1
endif
if !exists("g:jedi#goto_command")
    let g:jedi#goto_command = "<leader>g"
endif
if !exists("g:jedi#get_definition_command")
    let g:jedi#get_definition_command = "<leader>d"
endif
if !exists("g:jedi#related_names_command")
    let g:jedi#related_names_command = "<leader>n"
endif
if !exists("g:jedi#rename_command")
    let g:jedi#rename_command = "<leader>r"
endif
if !exists("g:jedi#popup_on_dot")
    let g:jedi#popup_on_dot = 1
endif
if !exists("g:jedi#pydoc")
    let g:jedi#pydoc = "K"
endif
if !exists("g:jedi#show_function_definition")
    let g:jedi#show_function_definition = 1
endif
if !exists("g:jedi#function_definition_escape")
    let g:jedi#function_definition_escape = '≡'
endif
if !exists("g:jedi#auto_close_doc")
    let g:jedi#auto_close_doc = 1
endif

set switchbuf=useopen  " needed for pydoc
let s:current_file=expand("<sfile>")

if g:jedi#auto_initialization 
    autocmd FileType python setlocal omnifunc=jedi#complete
endif



python << PYTHONEOF
""" here we initialize the jedi stuff """
import vim

# update the system path, to include the python scripts 
import sys
import os
from os.path import dirname, abspath, join
sys.path.insert(0, join(dirname(dirname(abspath(vim.eval('s:current_file')))), 'jedi'))

import jedi
import jedi.keywords

sys.path.append(dirname(abspath(vim.eval('s:current_file'))))
from jedi_vim import *
sys.path.pop()

PYTHONEOF

" vim: set et ts=4:
