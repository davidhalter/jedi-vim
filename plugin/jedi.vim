"py_fuzzycomplete.vim - Omni Completion for python in vim
" Maintainer: David Halter <davidhalter88@gmail.com>
" Version: 0.1
"
" This part of the software is just the vim interface. The main source code
" lies in the python files around it.

if !has('python') && !has('python3')
    if !exists("g:jedi#squelch_py_warning")
        echomsg "Error: Required vim compiled with +python"
    endif
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
    \ 'auto_vim_configuration': 1,
    \ 'goto_command': "'<leader>g'",
    \ 'autocompletion_command': "'<C-Space>'",
    \ 'get_definition_command': "'<leader>d'",
    \ 'related_names_command': "'<leader>n'",
    \ 'rename_command': "'<leader>r'",
    \ 'popup_on_dot': 1,
    \ 'pydoc': "'K'",
    \ 'show_function_definition': 1,
    \ 'function_definition_escape': "'≡'",
    \ 'auto_close_doc': 1,
    \ 'popup_select_first': 1
\ }

for [key, val] in items(s:settings)
    if !exists('g:jedi#'.key)
        exe 'let g:jedi#'.key.' = '.val
    endif
endfor


if g:jedi#auto_initialization 
    " this is only here because in some cases the VIM library adds their
    " autocompletion as a default, which may cause problems, depending on the
    " order of invocation.
    autocmd FileType Python setlocal omnifunc=jedi#complete switchbuf=useopen  " needed for pydoc
endif
" vim: set et ts=4:
