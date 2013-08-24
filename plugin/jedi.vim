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


" ------------------------------------------------------------------------
" deprecations
" ------------------------------------------------------------------------

let s:deprecations = {
    \ 'get_definition_command':     'goto_definitions_command',
    \ 'goto_command':               'goto_assignments_command',
    \ 'pydoc':                      'documentation_command',
    \ 'related_names_command':      'usages_command',
    \ 'autocompletion_command':     'completions_command',
    \ 'show_function_definition':   'show_call_signatures',
\ }

for [key, val] in items(s:deprecations)
    if exists('g:jedi#'.key)
        echom "'g:jedi#".key."' is deprecated. Please use 'g:jedi#".value."' instead. Sorry for the inconvenience."
        exe 'let g:jedi#'.val.' = g:jedi#'.key
    end
endfor


" ------------------------------------------------------------------------
" defaults for jedi-vim
" ------------------------------------------------------------------------

let s:settings = {
    \ 'use_tabs_not_buffers': 1,
    \ 'auto_initialization': 1,
    \ 'auto_vim_configuration': 1,
    \ 'goto_assignments_command': "'<leader>g'",
    \ 'completions_command': "'<C-Space>'",
    \ 'goto_definitions_command': "'<leader>d'",
    \ 'call_signatures_command': "'<leader>n'",
    \ 'usages_command': "'<leader>n'",
    \ 'rename_command': "'<leader>r'",
    \ 'popup_on_dot': 1,
    \ 'documentation_command': "'K'",
    \ 'show_call_signatures': 1,
    \ 'call_signature_escape': "'≡'",
    \ 'auto_close_doc': 1,
    \ 'popup_select_first': 1,
    \ 'quickfix_window_height': 10,
    \ 'completions_enabled': 1
\ }

for [key, val] in items(s:settings)
    if !exists('g:jedi#'.key)
        exe 'let g:jedi#'.key.' = '.val
    endif
endfor


if g:jedi#auto_vim_configuration
    filetype plugin on
endif
if g:jedi#auto_initialization 
    " this is only here because in some cases the VIM library adds their
    " autocompletion as a default, which may cause problems, depending on the
    " order of invocation.
    if g:jedi#completions_enabled
        autocmd FileType Python setlocal omnifunc=jedi#completions switchbuf=useopen  " needed for documentation/pydoc
    endif
endif


" ------------------------------------------------------------------------
" PyImport command
" ------------------------------------------------------------------------
command! -nargs=1 -complete=custom,jedi#py_import_completions Pyimport :call jedi#py_import(<q-args>)

" vim: set et ts=4:
