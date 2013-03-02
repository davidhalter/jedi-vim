"py_fuzzycomplete.vim - Omni Completion for python in vim
" Maintainer: David Halter <davidhalter88@gmail.com>
" Version: 0.1
"
" This part of the software is just the vim interface. The main source code
" lies in the python files around it.
"
let b:did_ftplugin = 1

if !has('python') && !has('python3')
    if !exists("g:jedi#squelch_py_warning")
        echomsg "Error: Required vim compiled with +python"
    endif
    finish
endif

" ------------------------------------------------------------------------
" Initialization of jedi-vim
" ------------------------------------------------------------------------
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
    setlocal omnifunc=jedi#complete

    " map ctrl+space for autocompletion
    if g:jedi#autocompletion_command == "<C-Space>"
        " in terminals, <C-Space> sometimes equals <Nul>
        inoremap <buffer><Nul> <C-X><C-O>
    endif
    execute "inoremap <buffer>".g:jedi#autocompletion_command." <C-X><C-O>"

    " goto / get_definition / related_names
    execute "noremap <buffer>".g:jedi#goto_command." :call jedi#goto()<CR>"
    execute "noremap <buffer>".g:jedi#get_definition_command." :call jedi#get_definition()<CR>"
    execute "noremap <buffer>".g:jedi#related_names_command." :call jedi#related_names()<CR>"
    " rename
    execute "noremap <buffer>".g:jedi#rename_command." :call jedi#rename()<CR>"
    " pydoc
    execute "nnoremap <silent> <buffer>".g:jedi#pydoc." :call jedi#show_pydoc()<CR>"

    if g:jedi#show_function_definition == 1 && has('conceal')
        call jedi#configure_function_definition()
    endif
end

if g:jedi#auto_vim_configuration
    setlocal completeopt=menuone,longest,preview
    if len(mapcheck('<C-c>', 'i')) == 0
        inoremap <C-c> <ESC>
    end
end

if g:jedi#popup_on_dot
    if stridx(&completeopt, 'longest') > -1
        if g:jedi#popup_select_first
            inoremap <buffer> . .<C-R>=jedi#do_popup_on_dot() ? "\<lt>C-X>\<lt>C-O>\<lt>C-N>" : ""<CR>
        else
            inoremap <buffer> . .<C-R>=jedi#do_popup_on_dot() ? "\<lt>C-X>\<lt>C-O>" : ""<CR>
        end

    else
        inoremap <buffer> . .<C-R>=jedi#do_popup_on_dot() ? "\<lt>C-X>\<lt>C-O>\<lt>C-P>" : ""<CR>
    end
end

if g:jedi#auto_close_doc
    " close preview if its still open after insert
    autocmd InsertLeave <buffer> if pumvisible() == 0|pclose|endif
end
