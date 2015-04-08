scriptencoding utf-8

" ------------------------------------------------------------------------
" functions that call python code
" ------------------------------------------------------------------------
function! jedi#goto_assignments()
    Python jedi_vim.goto()
endfunction

function! jedi#goto_definitions()
    Python jedi_vim.goto(is_definition=True)
endfunction

function! jedi#usages()
    Python jedi_vim.goto(is_related_name=True)
endfunction

function! jedi#rename(...)
    Python jedi_vim.rename()
endfunction

function! jedi#completions(findstart, base)
    Python jedi_vim.completions()
endfunction

function! jedi#enable_speed_debugging()
    Python jedi_vim.jedi.set_debug_function(jedi_vim.print_to_stdout, speed=True, warnings=False, notices=False)
endfunction

function! jedi#enable_debugging()
    Python jedi_vim.jedi.set_debug_function(jedi_vim.print_to_stdout)
endfunction

function! jedi#disable_debugging()
    Python jedi_vim.jedi.set_debug_function(None)
endfunction

function! jedi#py_import(args)
    Python jedi_vim.py_import()
endfun

function! jedi#py_import_completions(argl, cmdl, pos)
    Python jedi_vim.py_import_completions()
endfun


" ------------------------------------------------------------------------
" show_documentation
" ------------------------------------------------------------------------
function! jedi#show_documentation()
    Python if jedi_vim.show_documentation() is None: vim.command('return')

    let bn = bufnr("__doc__")
    if bn > 0
        let wi=index(tabpagebuflist(tabpagenr()), bn)
        if wi >= 0
            " If the __doc__ buffer is open in the current tab, jump to it
            silent execute (wi+1).'wincmd w'
        else
            silent execute "sbuffer ".bn
        endif
    else
        split '__doc__'
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

    if l:doc_lines > 30  " max lines for plugin
        let l:doc_lines = 30
    endif
    execute "resize ".l:doc_lines

    " quit comands
    nnoremap <buffer> q ZQ
    execute "nnoremap <buffer> ".g:jedi#documentation_command." ZQ"

    " highlight python code within rst
    unlet! b:current_syntax
    syn include @rstPythonScript syntax/python.vim
    " 4 spaces
    syn region rstPythonRegion start=/^\v {4}/ end=/\v^( {4}|\n)@!/ contains=@rstPythonScript
    " >>> python code -> (doctests)
    syn region rstPythonRegion matchgroup=pythonDoctest start=/^>>>\s*/ end=/\n/ contains=@rstPythonScript
    let b:current_syntax = "rst"
endfunction

" ------------------------------------------------------------------------
" helper functions
" ------------------------------------------------------------------------

function! jedi#add_goto_window(len)
    set lazyredraw
    cclose
    let height = min([a:len, g:jedi#quickfix_window_height])
    execute 'belowright copen '.height
    set nolazyredraw
    if g:jedi#use_tabs_not_buffers == 1
        noremap <buffer> <CR> :call jedi#goto_window_on_enter()<CR>
    endif
    au WinLeave <buffer> q  " automatically leave, if an option is chosen
    redraw!
endfunction


function! jedi#goto_window_on_enter()
    let l:list = getqflist()
    let l:data = l:list[line('.') - 1]
    if l:data.bufnr
        " close goto_window buffer
        normal ZQ
        Python jedi_vim.new_buffer(vim.eval('bufname(l:data.bufnr)'))
        call cursor(l:data.lnum, l:data.col)
    else
        echohl WarningMsg | echo "Builtin module cannot be opened." | echohl None
    endif
endfunction


function! s:syn_stack()
    if !exists("*synstack")
        return []
    endif
    return map(synstack(line('.'), col('.') - 1), 'synIDattr(v:val, "name")')
endfunc


function! jedi#do_popup_on_dot_in_highlight()
    let highlight_groups = s:syn_stack()
    for a in highlight_groups
        if a == 'pythonDoctest'
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


function! jedi#configure_call_signatures()
    if g:jedi#show_call_signatures == 2  " Command line call signatures
        " Need to track changes to avoid multiple undo points for a single edit
        if v:version >= 704 || has("patch-7.3.867")
            let b:normaltick = b:changedtick
            autocmd TextChanged,InsertLeave,BufWinEnter <buffer> let b:normaltick = b:changedtick
        endif
        autocmd InsertEnter <buffer> let g:jedi#first_col = s:save_first_col()
    endif
    autocmd InsertLeave <buffer> Python jedi_vim.clear_call_signatures()
    autocmd CursorMovedI <buffer> Python jedi_vim.show_call_signatures()
endfunction

" Determine where the current window is on the screen for displaying call
" signatures in the correct column.
function! s:save_first_col()
    if bufname('%') ==# '[Command Line]' || winnr('$') == 1
        return 0
    endif

    let l:eventignore = &eventignore
    set eventignore=all
    let startwin = winnr()
    let startaltwin = winnr('#')
    let winwidth = winwidth(0)

    try
        wincmd h
        let win_on_left = winnr() == startwin
        if win_on_left
            return 0
        else
            " Walk left and count up window widths until hitting the edge
            execute startwin."wincmd w"
            let width = 0
            let winnr = winnr()
            wincmd h
            while winnr != winnr()
                let width += winwidth(0) + 1  " Extra column for window divider
                let winnr = winnr()
                wincmd h
            endwhile
            return width
        endif
    finally
        let &eventignore = l:eventignore
        execute startaltwin."wincmd w"
        execute startwin."wincmd w"
        " If the event that triggered InsertEnter made a change (e.g. open a
        " new line, substitude a word), join that change with the rest of this
        " edit.
        if exists('b:normaltick') && b:normaltick != b:changedtick
            try
                undojoin
            catch /^Vim\%((\a\+)\)\=:E790/
                " This can happen if an undo happens during a :normal command.
            endtry
        endif
    endtry
endfunction

" Helper function instead of `python vim.eval()`, and `.command()` because
" these also return error definitions.
function! jedi#_vim_exceptions(str, is_eval)
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


function! jedi#complete_string(is_popup_on_dot)

    if a:is_popup_on_dot && !(g:jedi#popup_on_dot && jedi#do_popup_on_dot_in_highlight())
        return ''

    end
    if pumvisible() && !a:is_popup_on_dot
        return "\<C-n>"
    else
        return "\<C-x>\<C-o>\<C-r>=jedi#complete_opened()\<CR>"
    end
endfunction


function! jedi#complete_opened()
    if pumvisible() && g:jedi#popup_select_first && stridx(&completeopt, 'longest') > -1
        " only go down if it is visible, user-enabled and the longest option is set
        return "\<Down>"
    end
    return ""
endfunction


function! jedi#force_py_version(py_version)
    let g:jedi#force_py_version = a:py_version
    if g:jedi#force_py_version == 2
        command! -nargs=1 Python python <args>
        execute 'pyfile '.s:script_path.'/initialize.py'
    elseif g:jedi#force_py_version == 3
        command! -nargs=1 Python python3 <args>
        execute 'py3file '.s:script_path.'/initialize.py'
    endif
endfunction


function! jedi#force_py_version_switch()
    if g:jedi#force_py_version == 2
        call jedi#force_py_version(3)
    elseif g:jedi#force_py_version == 3
        call jedi#force_py_version(2)
    endif
endfunction


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

" ------------------------------------------------------------------------
" defaults for jedi-vim
" ------------------------------------------------------------------------
let s:settings = {
    \ 'use_tabs_not_buffers': 1,
    \ 'use_splits_not_buffers': 1,
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
    \ 'call_signature_escape': "'=`='",
    \ 'auto_close_doc': 1,
    \ 'popup_select_first': 1,
    \ 'quickfix_window_height': 10,
    \ 'completions_enabled': 1,
    \ 'force_py_version': 2
\ }


function! s:init()
  for [key, val] in items(s:deprecations)
      if exists('g:jedi#'.key)
          echom "'g:jedi#".key."' is deprecated. Please use 'g:jedi#".val."' instead. Sorry for the inconvenience."
          exe 'let g:jedi#'.val.' = g:jedi#'.key
      end
  endfor

  for [key, val] in items(s:settings)
      if !exists('g:jedi#'.key)
          exe 'let g:jedi#'.key.' = '.val
      endif
  endfor
endfunction


call s:init()

" ------------------------------------------------------------------------
" Python initialization
" ------------------------------------------------------------------------

let s:script_path = fnameescape(expand('<sfile>:p:h:h'))

if has('python') && has('python3')
    call jedi#force_py_version(g:jedi#force_py_version)
elseif has('python')
    command! -nargs=1 Python python <args>
    execute 'pyfile '.s:script_path.'/initialize.py'
elseif has('python3')
    command! -nargs=1 Python python3 <args>
    execute 'py3file '.s:script_path.'/initialize.py'
else
    if !exists("g:jedi#squelch_py_warning")
        echomsg "Error: jedi-vim requires vim compiled with +python"
    endif
    finish
end


"Python jedi_vim.jedi.set_debug_function(jedi_vim.print_to_stdout, speed=True, warnings=False, notices=False)
"Python jedi_vim.jedi.set_debug_function(jedi_vim.print_to_stdout)

" vim: set et ts=4:
