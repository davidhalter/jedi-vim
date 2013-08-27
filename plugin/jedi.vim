"jedi.vim - Omni Completion for python in vim
" Maintainer: David Halter <davidhalter88@gmail.com>
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


if g:jedi#auto_vim_configuration
    filetype plugin on
endif


" ------------------------------------------------------------------------
" PyImport command
" ------------------------------------------------------------------------
command! -nargs=1 -complete=custom,jedi#py_import_completions Pyimport :call jedi#py_import(<q-args>)

" vim: set et ts=4:
