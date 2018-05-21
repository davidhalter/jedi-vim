scriptencoding utf-8

" ------------------------------------------------------------------------
" Settings initialization
" ------------------------------------------------------------------------
let s:deprecations = {
    \ 'get_definition_command':     'goto_definitions_command',
    \ 'pydoc':                      'documentation_command',
    \ 'related_names_command':      'usages_command',
    \ 'autocompletion_command':     'completions_command',
    \ 'show_function_definition':   'show_call_signatures',
\ }

let s:default_settings = {
    \ 'use_tabs_not_buffers': 0,
    \ 'use_splits_not_buffers': 1,
    \ 'auto_initialization': 1,
    \ 'auto_vim_configuration': 1,
    \ 'goto_command': "'<leader>d'",
    \ 'goto_assignments_command': "'<leader>g'",
    \ 'goto_definitions_command': "''",
    \ 'completions_command': "'<C-Space>'",
    \ 'call_signatures_command': "'<leader>n'",
    \ 'usages_command': "'<leader>n'",
    \ 'rename_command': "'<leader>r'",
    \ 'completions_enabled': 1,
    \ 'popup_on_dot': 'g:jedi#completions_enabled',
    \ 'documentation_command': "'K'",
    \ 'show_call_signatures': 1,
    \ 'show_call_signatures_delay': 500,
    \ 'call_signature_escape': "'?!?'",
    \ 'auto_close_doc': 1,
    \ 'max_doc_height': 30,
    \ 'popup_select_first': 1,
    \ 'quickfix_window_height': 10,
    \ 'force_py_version': "'auto'",
    \ 'smart_auto_mappings': 1,
    \ 'use_tag_stack': 1
\ }

for [s:key, s:val] in items(s:deprecations)
    if exists('g:jedi#'.s:key)
        echom "'g:jedi#".s:key."' is deprecated. Please use 'g:jedi#".s:val."' instead. Sorry for the inconvenience."
        exe 'let g:jedi#'.s:val.' = g:jedi#'.s:key
    endif
endfor

for [s:key, s:val] in items(s:default_settings)
    if !exists('g:jedi#'.s:key)
        exe 'let g:jedi#'.s:key.' = '.s:val
    endif
endfor


" ------------------------------------------------------------------------
" Python initialization
" ------------------------------------------------------------------------
let s:script_path = fnameescape(expand('<sfile>:p:h:h'))

function! s:init_python() abort
    if has('python3')
        call jedi#setup_python_imports(3)
    elseif has('python')
        call jedi#setup_python_imports(2)
    else
        throw 'jedi-vim requires Vim with support for Python 2 or 3.'
    endif
    return 1
endfunction


function! jedi#reinit_python() abort
    unlet! s:_init_python
    call jedi#init_python()
endfunction


let s:_init_python = -1
function! jedi#init_python() abort
    if s:_init_python == -1
        try
            let s:_init_python = s:init_python()
        catch
            let s:_init_python = 0
            if !exists('g:jedi#squelch_py_warning')
                echoerr 'Error: jedi-vim failed to initialize Python: '
                            \ .v:exception.' (in '.v:throwpoint.')'
            endif
        endtry
    endif
    return s:_init_python
endfunction


let s:python_version = 'null'
function! jedi#setup_python_imports(py_version) abort
    if a:py_version == 2
        let cmd_exec = 'python'
        let s:python_version = 2
    elseif a:py_version == 3
        let cmd_exec = 'python3'
        let s:python_version = 3
    else
        throw 'jedi#setup_python_imports: invalid py_version: '.a:py_version
    endif

    execute 'command! -nargs=1 PythonJedi '.cmd_exec.' <args>'

    let s:init_outcome = 0
    let init_lines = [
          \ 'import vim',
          \ 'try:',
          \ '    import jedi_vim',
          \ 'except Exception as exc:',
          \ '    vim.command(''let s:init_outcome = "could not import jedi_vim: {0}: {1}"''.format(exc.__class__.__name__, exc))',
          \ 'else:',
          \ '    vim.command(''let s:init_outcome = 1'')']
    try
        exe 'PythonJedi exec('''.escape(join(init_lines, '\n'), "'").''')'
    catch
        throw printf('jedi#setup_python_imports: failed to run Python for initialization: %s.', v:exception)
    endtry
    if s:init_outcome is 0
        throw 'jedi#setup_python_imports: failed to run Python for initialization.'
    elseif s:init_outcome isnot 1
        throw printf('jedi#setup_python_imports: %s.', s:init_outcome)
    endif
    return 1
endfunction


function! jedi#debug_info() abort
    if s:python_version ==# 'null'
        try
            call s:init_python()
        catch
            echohl WarningMsg | echom v:exception | echohl None
            return
        endtry
    endif
    if &verbose
      if &filetype !=# 'python'
        echohl WarningMsg | echo 'You should run this in a buffer with filetype "python".' | echohl None
      endif
    endif
    echo '#### Jedi-vim debug information'
    echo 'Using Python version:' s:python_version
    let pyeval = s:python_version == 3 ? 'py3eval' : 'pyeval'
    let s:pythonjedi_called = 0
    PythonJedi import vim; vim.command('let s:pythonjedi_called = 1')
    if !s:pythonjedi_called
      echohl WarningMsg
      echom 'PythonJedi failed to run, likely a Python config issue.'
      if exists(':CheckHealth') == 2
        echom 'Try :CheckHealth for more information.'
      endif
      echohl None
    else
      PythonJedi from jedi_vim_debug import display_debug_info
      PythonJedi display_debug_info()
    endif
    echo ' - jedi-vim git version: '
    echon substitute(system('git -C '.s:script_path.' describe --tags --always --dirty'), '\v\n$', '', '')
    echo ' - jedi git submodule status: '
    echon substitute(system('git -C '.s:script_path.' submodule status'), '\v\n$', '', '')
    echo "\n"
    echo '##### Settings'
    echo '```'
    let jedi_settings = items(filter(copy(g:), "v:key =~# '\\v^jedi#'"))
    let has_nondefault_settings = 0
    for [k, V] in jedi_settings
      exe 'let default = '.get(s:default_settings,
            \ substitute(k, '\v^jedi#', '', ''), "'-'")
      " vint: -ProhibitUsingUndeclaredVariable
      if default !=# V
        echo printf('g:%s = %s (default: %s)', k, string(V), string(default))
        unlet! V  " Fix variable type mismatch with Vim 7.3.
        let has_nondefault_settings = 1
      endif
      " vint: +ProhibitUsingUndeclaredVariable
    endfor
    if has_nondefault_settings
      echo "\n"
    endif
    verb set omnifunc? completeopt?
    echo '```'

    if &verbose
      echo "\n"
      echo '#### :version'
      echo '```'
      version
      echo '```'
      echo "\n"
      echo '#### :messages'
      echo '```'
      messages
      echo '```'
      echo "\n"
      echo '<details><summary>:scriptnames</summary>'
      echo "\n"
      echo '```'
      scriptnames
      echo '```'
      echo '</details>'
    endif
endfunction

" Helper function instead of `python vim.eval()`, and `.command()` because
" these also return error definitions.
function! jedi#_vim_exceptions(str, is_eval) abort
    let l:result = {}
    try
        if a:is_eval
            let l:result.result = eval(a:str)
        else
            execute a:str
            let l:result.result = ''
        endif
    catch
        let l:result.exception = v:exception
        let l:result.throwpoint = v:throwpoint
    endtry
    return l:result
endfunction

call jedi#init_python()  " Might throw an error.

" ------------------------------------------------------------------------
" functions that call python code
" ------------------------------------------------------------------------
function! jedi#goto() abort
    PythonJedi jedi_vim.goto(mode="goto")
endfunction

function! jedi#goto_assignments() abort
    PythonJedi jedi_vim.goto(mode="assignment")
endfunction

function! jedi#goto_definitions() abort
    PythonJedi jedi_vim.goto(mode="definition")
endfunction

function! jedi#usages() abort
    PythonJedi jedi_vim.goto(mode="related_name")
endfunction

function! jedi#rename(...) abort
    PythonJedi jedi_vim.rename()
endfunction

function! jedi#rename_visual(...) abort
    PythonJedi jedi_vim.rename_visual()
endfunction

function! jedi#completions(findstart, base) abort
    PythonJedi jedi_vim.completions()
endfunction

function! jedi#enable_speed_debugging() abort
    PythonJedi jedi_vim.jedi.set_debug_function(jedi_vim.print_to_stdout, speed=True, warnings=False, notices=False)
endfunction

function! jedi#enable_debugging() abort
    PythonJedi jedi_vim.jedi.set_debug_function(jedi_vim.print_to_stdout)
endfunction

function! jedi#disable_debugging() abort
    PythonJedi jedi_vim.jedi.set_debug_function(None)
endfunction

function! jedi#py_import(args) abort
    PythonJedi jedi_vim.py_import()
endfun

function! jedi#py_import_completions(argl, cmdl, pos) abort
    PythonJedi jedi_vim.py_import_completions()
endfun

function! jedi#clear_cache(bang) abort
    PythonJedi jedi_vim.jedi.cache.clear_time_caches(True)
    if a:bang
        PythonJedi jedi_vim.jedi.parser.utils.ParserPickling.clear_cache()
    endif
endfunction


" ------------------------------------------------------------------------
" show_documentation
" ------------------------------------------------------------------------
function! jedi#show_documentation() abort
    PythonJedi if jedi_vim.show_documentation() is None: vim.command('return')

    let bn = bufnr('__doc__')
    if bn > 0
        let wi=index(tabpagebuflist(tabpagenr()), bn)
        if wi >= 0
            " If the __doc__ buffer is open in the current tab, jump to it
            silent execute (wi+1).'wincmd w'
        else
            silent execute 'sbuffer '.bn
        endif
    else
        split __doc__
    endif

    setlocal modifiable
    setlocal noswapfile
    setlocal buftype=nofile
    silent normal! ggdG
    silent $put=l:doc
    silent normal! 1Gdd
    setlocal nomodifiable
    setlocal nomodified
    setlocal filetype=rst
    setlocal foldlevel=200 " do not fold in __doc__

    if l:doc_lines > g:jedi#max_doc_height " max lines for plugin
        let l:doc_lines = g:jedi#max_doc_height
    endif
    execute 'resize '.l:doc_lines

    " quit comands
    nnoremap <buffer> q ZQ
    execute 'nnoremap <buffer> '.g:jedi#documentation_command.' ZQ'
endfunction

" ------------------------------------------------------------------------
" helper functions
" ------------------------------------------------------------------------

function! jedi#add_goto_window(len) abort
    set lazyredraw
    cclose
    let height = min([a:len, g:jedi#quickfix_window_height])
    execute 'belowright copen '.height
    set nolazyredraw
    if g:jedi#use_tabs_not_buffers == 1
        noremap <buffer> <CR> :call jedi#goto_window_on_enter()<CR>
    endif
    augroup jedi_goto_window
      au!
      au WinLeave <buffer> q  " automatically leave, if an option is chosen
    augroup END
    redraw!
endfunction


function! jedi#goto_window_on_enter() abort
    let l:list = getqflist()
    let l:data = l:list[line('.') - 1]
    if l:data.bufnr
        " close goto_window buffer
        normal! ZQ
        PythonJedi jedi_vim.new_buffer(vim.eval('bufname(l:data.bufnr)'))
        call cursor(l:data.lnum, l:data.col)
    else
        echohl WarningMsg | echo 'Builtin module cannot be opened.' | echohl None
    endif
endfunction


function! s:syn_stack() abort
    if !exists('*synstack')
        return []
    endif
    return map(synstack(line('.'), col('.') - 1), "synIDattr(v:val, 'name')")
endfunc


function! jedi#do_popup_on_dot_in_highlight() abort
    let highlight_groups = s:syn_stack()
    for a in highlight_groups
        if a ==# 'pythonDoctest'
            return 1
        endif
    endfor

    for a in highlight_groups
        for b in ['pythonString', 'pythonComment', 'pythonNumber']
            if a == b
                return 0
            endif
        endfor
    endfor
    return 1
endfunc


let s:show_call_signatures_last = [0, 0, '']
function! jedi#show_call_signatures() abort
    if s:_init_python == 0
        return 1
    endif
    let [line, col] = [line('.'), col('.')]
    let curline = getline(line)
    let reload_signatures = 1

    " Caching.  On the same line only.
    if line == s:show_call_signatures_last[0]
        " Check if the number of commas and parenthesis before or after the
        " cursor has not changed since the last call, which means that the
        " argument position was not changed and we can skip repainting.
        let prevcol = s:show_call_signatures_last[1]
        let prevline = s:show_call_signatures_last[2]
        if substitute(curline[:col-2], '[^,()]', '', 'g')
                    \ == substitute(prevline[:prevcol-2], '[^,()]', '', 'g')
                    \ && substitute(curline[(col-2):], '[^,()]', '', 'g')
                    \ == substitute(prevline[(prevcol-2):], '[^,()]', '', 'g')
            let reload_signatures = 0
        endif
    endif
    let s:show_call_signatures_last = [line, col, curline]

    if reload_signatures
        PythonJedi jedi_vim.show_call_signatures()
    endif
endfunction


function! jedi#clear_call_signatures() abort
    if s:_init_python == 0
        return 1
    endif

    let s:show_call_signatures_last = [0, 0, '']
    PythonJedi jedi_vim.clear_call_signatures()
endfunction


function! jedi#configure_call_signatures() abort
    augroup jedi_call_signatures
    autocmd! * <buffer>
    if g:jedi#show_call_signatures == 2  " Command line call signatures
        autocmd InsertEnter <buffer> let g:jedi#first_col = s:save_first_col()
    endif
    autocmd InsertEnter <buffer> let s:show_call_signatures_last = [0, 0, '']
    autocmd InsertLeave <buffer> call jedi#clear_call_signatures()
    if g:jedi#show_call_signatures_delay > 0
        autocmd InsertEnter <buffer> let b:_jedi_orig_updatetime = &updatetime
                    \ | let &updatetime = g:jedi#show_call_signatures_delay
        autocmd InsertLeave <buffer> if exists('b:_jedi_orig_updatetime')
                    \ |   let &updatetime = b:_jedi_orig_updatetime
                    \ |   unlet b:_jedi_orig_updatetime
                    \ | endif
        autocmd CursorHoldI <buffer> call jedi#show_call_signatures()
    else
        autocmd CursorMovedI <buffer> call jedi#show_call_signatures()
    endif
    augroup END
endfunction


" Determine where the current window is on the screen for displaying call
" signatures in the correct column.
function! s:save_first_col() abort
    if bufname('%') ==# '[Command Line]' || winnr('$') == 1
        return 0
    endif

    let startwin = winnr()
    let winwidth = winwidth(0)
    if winwidth == &columns
        return 0
    elseif winnr('$') == 2
        return startwin == 1 ? 0 : (winwidth(1) + 1)
    elseif winnr('$') == 3
        if startwin == 1
            return 0
        endif
        let ww1 = winwidth(1)
        let ww2 = winwidth(2)
        let ww3 = winwidth(3)
        if ww1 + ww2 + ww3 + 2 == &columns
            if startwin == 2
                return ww1 + 1
            else
                return ww1 + ww2 + 2
            endif
        elseif startwin == 2
            if ww2 + ww3 + 1 == &columns
                return 0
            else
                return ww1 + 1
            endif
        else " startwin == 3
            if ww2 + ww3 + 1 == &columns
                return ww2 + 1
            else
                return ww1 + 1
            endif
        endif
    endif
    return 0
endfunction


function! jedi#complete_string(autocomplete) abort
    if a:autocomplete
        if !(g:jedi#popup_on_dot && jedi#do_popup_on_dot_in_highlight())
            return ''
        endif

        let s:saved_completeopt = &completeopt
        set completeopt-=longest
        set completeopt+=menuone
        set completeopt-=menu
        if &completeopt !~# 'noinsert\|noselect'
            " Patch 775 introduced noinsert and noselect, previously these
            " options didn't exist. Setting them in earlier versions results in
            " errors (E474).
            if has('patch-7.4-775')
                if g:jedi#popup_select_first
                    set completeopt+=noinsert
                else
                    set completeopt+=noselect
                endif
            else
                " To pass the tests we use this, it seems to get the closest to
                " the other options. I'm really not sure if this properly
                " works, but VIM 7.4-775 is already pretty old, so it might not
                " be a problem anymore in a few years.
                set completeopt+=longest
            endif
        endif
    elseif pumvisible()
        return "\<C-n>"
    endif
    return "\<C-x>\<C-o>\<C-r>=jedi#complete_opened(".a:autocomplete.")\<CR>"
endfunction


function! jedi#complete_opened(autocomplete) abort
    if a:autocomplete
        let &completeopt = s:saved_completeopt
        unlet s:saved_completeopt
    elseif pumvisible() && g:jedi#popup_select_first && stridx(&completeopt, 'longest') > -1
        return "\<Down>"
    endif
    return ''
endfunction


function! jedi#smart_auto_mappings() abort
    " Auto put import statement after from module.name<space> and complete
    if search('\m^\s*from\s\+[A-Za-z0-9._]\{1,50}\%#\s*$', 'bcn', line('.'))
        " Enter character and start completion.
        return "\<space>import \<C-r>=jedi#complete_string(1)\<CR>"
    endif
    return "\<space>"
endfunction


function! jedi#setup_completion() abort
    " We need our own omnifunc, so this overrides the omnifunc set by
    " $VIMRUNTIME/ftplugin/python.vim.
    setlocal omnifunc=jedi#completions

    " map ctrl+space for autocompletion
    if g:jedi#completions_command ==# '<C-Space>'
        " In terminals, <C-Space> sometimes equals <Nul>.
        imap <buffer> <Nul> <C-Space>
        smap <buffer> <Nul> <C-Space>
    endif
    if len(g:jedi#completions_command)
        execute 'inoremap <expr> <buffer> '.g:jedi#completions_command.' jedi#complete_string(0)'
        " A separate mapping for select mode: deletes and completes.
        execute 'snoremap <expr> <buffer> '.g:jedi#completions_command." '\<C-g>c'.jedi#complete_string(0)"
    endif
endfunction

"PythonJedi jedi_vim.jedi.set_debug_function(jedi_vim.print_to_stdout, speed=True, warnings=False, notices=False)
"PythonJedi jedi_vim.jedi.set_debug_function(jedi_vim.print_to_stdout)

" vim: set et ts=4:
