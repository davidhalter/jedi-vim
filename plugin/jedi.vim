"jedi-vim - Omni Completion for python in vim
" Maintainer: David Halter <davidhalter88@gmail.com>
"
" This part of the software is just the vim interface. The really big deal is
" the Jedi Python library.


" jedi-vim doesn't work in compatible mode (vim script syntax problems)
if &compatible
    set nocompatible
endif

" jedi-vim really needs, otherwise jedi-vim cannot start.
filetype plugin on

" Pyimport command
command! -nargs=1 -complete=custom,jedi#py_import_completions Pyimport :call jedi#py_import(<q-args>)

" vim: set et ts=4:
