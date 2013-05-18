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
    \ 'popup_select_first': 1,
    \ 'quickfix_window_height': 10
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

fun! Pyimport(cmd, args)
py << EOF
    # args are the same as for the :edit command
    # cmd: one of edit, split, vsplit, tabedit, ...
if 1:
    import vim
    import jedi
    import os.path as osp
    from shlex import split as shsplit

    cmd = vim.eval('a:cmd')
    args = shsplit(vim.eval('a:args'))
    text = 'import %s' % args.pop()
    scr = jedi.Script(text, 1, len(text), '')
    try:
        path = scr.goto()[0].module_path
    except IndexError:
        path = None
    if path and osp.isfile(path):
        cmd_args = ' '.join([a.replace(' ', '\\ ') for a in args])
        vim.command('%s %s %s' % (cmd, cmd_args , path.replace(' ', '\ ')))
EOF
endfun

fun! Pyimport_comp(argl, cmdl, pos)
py << EOF
if 1:
    import vim
    import re
    import json
    argl = vim.eval('a:argl')
    try:
        import jedi
    except ImportError as err:
        print('Pyimport completion requires jedi module: https://github.com/davidhalter/jedi')
        comps = []
    else:
        text = 'import %s' % argl
        script=jedi.Script(text, 1, len(text), '')
        comps = [ '%s%s' % (argl, c.complete) for c in script.complete()]
    vim.command("let comps = '%s'" % '\n'.join(comps))
EOF
    return comps
endfun

command! -nargs=1 -complete=custom,Pyimport_comp Pyimport :call Pyimport('edit', <q-args>)
" command! -nargs=1 -complete=custom,Pyimport_comp Pysplit :call Pyimport('split', <q-args>)
" command! -nargs=1 -complete=custom,Pyimport_comp Pyvsplit :call Pyimport('vsplit', <q-args>)
" command! -nargs=1 -complete=custom,Pyimport_comp Pytabe :call Pyimport('tabe', <q-args>)
" vim: set et ts=4:
