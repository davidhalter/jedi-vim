"jedi-vim - Omni Completion for python in vim
" Maintainer: David Halter <davidhalter88@gmail.com>
"
" This part of the software is just the vim interface. The really big deal is
" the Jedi Python library.

if get(g:, 'jedi#auto_vim_configuration', 1)
    " jedi-vim doesn't work in compatible mode (vim script syntax problems)
    if &compatible
        " vint: -ProhibitSetNoCompatible
        set nocompatible
        " vint: +ProhibitSetNoCompatible
    endif

    " jedi-vim really needs, otherwise jedi-vim cannot start.
    filetype plugin on

    " Change completeopt, but only if it was not set already.
    redir => completeopt
        silent verb set completeopt?
    redir END
    if len(split(completeopt, '\n')) == 1
        set completeopt=menuone,longest,preview
    endif

    if len(mapcheck('<C-c>', 'i')) == 0
        inoremap <C-c> <ESC>
    endif
endif

" Pyimport command
command! -nargs=1 -complete=custom,jedi#py_import_completions Pyimport :call jedi#py_import(<q-args>)

command! -nargs=0 -bar JediDebugInfo call jedi#debug_info()
command! -nargs=0 -bang JediClearCache call jedi#clear_cache(<bang>0)

" vim: set et ts=4:
