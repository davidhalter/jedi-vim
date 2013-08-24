let b:did_ftplugin = 1

if !has('python') && !has('python3')
    finish
endif
" ------------------------------------------------------------------------
" Initialization of jedi-vim
" ------------------------------------------------------------------------

if g:jedi#auto_initialization
    if g:jedi#completions_enabled
        setlocal omnifunc=jedi#completions

        " map ctrl+space for autocompletion
        if g:jedi#completions_command == "<C-Space>"
            " in terminals, <C-Space> sometimes equals <Nul>
            inoremap <expr> <Nul> pumvisible() \|\| &omnifunc == '' ?
                    \ "\<lt>C-n>" :
                    \ "\<lt>C-x>\<lt>C-o><c-r>=pumvisible() ?" .
                    \ "\"\\<lt>c-n>\\<lt>c-p>\\<lt>c-n>\" :" .
                    \ "\" \\<lt>bs>\\<lt>C-n>\"\<CR>"
        endif
        if g:jedi#completions_command != ""
            execute "inoremap <buffer>".g:jedi#completions_command." <C-X><C-O>"
        endif
    endif

    " goto / get_definition / usages
    if g:jedi#goto_assignments_command != ''
        execute "noremap <buffer>".g:jedi#goto_assignments_command." :call jedi#goto_assignments()<CR>"
    endif
    if g:jedi#goto_definitions_command != ''
        execute "noremap <buffer>".g:jedi#goto_definitions_command." :call jedi#goto_definitions()<CR>"
    endif
    if g:jedi#usages_command != ''
        execute "noremap <buffer>".g:jedi#usages_command." :call jedi#usages()<CR>"
    endif
    " rename
    if g:jedi#rename_command != ''
        execute "noremap <buffer>".g:jedi#rename_command." :call jedi#rename()<CR>"
    endif
    " documentation/pydoc
    if g:jedi#documentation_command != ''
        execute "nnoremap <silent> <buffer>".g:jedi#documentation_command." :call jedi#show_documentation()<CR>"
    endif

    if g:jedi#show_call_signatures == 1 && has('conceal')
        call jedi#configure_call_signatures()
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
            inoremap <silent> <buffer> . .<C-R>=jedi#do_popup_on_dot() ? "\<lt>C-X>\<lt>C-O>\<lt>C-N>" : ""<CR>
        else
            inoremap <silent> <buffer> . .<C-R>=jedi#do_popup_on_dot() ? "\<lt>C-X>\<lt>C-O>" : ""<CR>
        end

    else
        inoremap <silent> <buffer> . .<C-R>=jedi#do_popup_on_dot() ? "\<lt>C-X>\<lt>C-O>\<lt>C-P>" : ""<CR>
    end
end

if g:jedi#auto_close_doc
    " close preview if its still open after insert
    autocmd InsertLeave <buffer> if pumvisible() == 0|pclose|endif
end
