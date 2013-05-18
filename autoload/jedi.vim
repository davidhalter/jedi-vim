" ------------------------------------------------------------------------
" functions that call python code
" ------------------------------------------------------------------------
function! jedi#goto()
    Python jedi_vim.goto()
endfunction


function! jedi#get_definition()
    Python jedi_vim.goto(is_definition=True)
endfunction


function! jedi#related_names()
    Python jedi_vim.goto(is_related_name=True)
endfunction


function! jedi#rename(...)
    Python jedi_vim.rename()
endfunction


function! jedi#complete(findstart, base)
    Python jedi_vim.complete()
endfunction


function! jedi#show_func_def()
    Python jedi_vim.show_func_def()
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

" ------------------------------------------------------------------------
" show_pydoc
" ------------------------------------------------------------------------
function! jedi#show_pydoc()
    Python jedi_vim.show_pydoc()
    if bufnr("__doc__") > 0
        " If the __doc__ buffer is open in the current window, jump to it
        silent execute "sbuffer ".bufnr("__doc__")
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
    nnoremap <buffer> K ZQ

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
function! jedi#new_buffer(path)
    if g:jedi#use_tabs_not_buffers
        Python jedi_vim.tabnew(jedi_vim.escape_file_path(vim.eval('a:path')))
    else
        if !&hidden && &modified
            w
        endif
        Python vim.command('edit ' + jedi_vim.escape_file_path(vim.eval('a:path')))
    endif
    " sometimes syntax is being disabled and the filetype not set.
    if !exists("g:syntax_on")
      syntax enable
    endif
    if &filetype != 'python'
      set filetype=python
    endif
endfunction

function! jedi#add_goto_window()
    set lazyredraw
    cclose
    execute 'belowright copen '.g:jedi#quickfix_window_height
    set nolazyredraw
    if g:jedi#use_tabs_not_buffers == 1
        map <buffer> <CR> :call jedi#goto_window_on_enter()<CR>
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
        call jedi#new_buffer(bufname(l:data.bufnr))
        call cursor(l:data.lnum, l:data.col)
    else
        echohl WarningMsg | echo "Builtin module cannot be opened." | echohl None
    endif
endfunction


function! jedi#syn_stack()
    if !exists("*synstack")
        return []
    endif
    return map(synstack(line('.'), col('.') - 1), 'synIDattr(v:val, "name")')
endfunc


function! jedi#do_popup_on_dot()
    let highlight_groups = jedi#syn_stack()
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

function! jedi#configure_function_definition()
    autocmd InsertLeave <buffer> Python jedi_vim.clear_func_def()
    autocmd CursorMovedI <buffer> call jedi#show_func_def()
endfunction

if has('python')
    command! -nargs=1 Python python <args>
else
    command! -nargs=1 Python python3 <args>
end

Python << PYTHONEOF
""" here we initialize the jedi stuff """
import vim

# update the system path, to include the jedi path
import sys
import os
sys.path.insert(0, os.path.join(vim.eval('expand("<sfile>:p:h:h")'), 'jedi'))

# to display errors correctly
import traceback

# update the sys path to include the jedi_vim script
sys.path.insert(1, os.path.join(vim.eval('expand("<sfile>:p:h:h")'), 'plugin'))
import jedi_vim
sys.path.pop(1)

PYTHONEOF
"Python jedi_vim.jedi.set_debug_function(jedi_vim.print_to_stdout, speed=True, warnings=False, notices=False)
"Python jedi_vim.jedi.set_debug_function(jedi_vim.print_to_stdout)

" vim: set et ts=4:
