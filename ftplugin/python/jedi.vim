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
            inoremap <expr> <Nul> jedi#complete_string(0)
        endif
        if g:jedi#completions_command != ""
            execute "inoremap <expr> <buffer> ".g:jedi#completions_command." jedi#complete_string(0)"
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

    inoremap <silent> <buffer> . .<C-R>=jedi#complete_string(1)<CR>

    if g:jedi#auto_close_doc
        " close preview if its still open after insert
        autocmd InsertLeave <buffer> if pumvisible() == 0|pclose|endif
    end
end

if g:jedi#auto_vim_configuration
    setlocal completeopt=menuone,longest,preview
    if len(mapcheck('<C-c>', 'i')) == 0
        inoremap <C-c> <ESC>
    end
end
