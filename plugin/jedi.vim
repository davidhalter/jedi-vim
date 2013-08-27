"jedi.vim - Omni Completion for python in vim
" Maintainer: David Halter <davidhalter88@gmail.com>
"
" This part of the software is just the vim interface. The really big deal is
" the Jedi Python library.

if g:jedi#auto_vim_configuration
    filetype plugin on
endif

" ------------------------------------------------------------------------
" PyImport command
" ------------------------------------------------------------------------
command! -nargs=1 -complete=custom,jedi#py_import_completions Pyimport :call jedi#py_import(<q-args>)

" vim: set et ts=4:
