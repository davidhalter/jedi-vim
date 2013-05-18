let b:did_ftplugin = 1

if !has('python') && !has('python3')
    finish
endif
" ------------------------------------------------------------------------
" Initialization of jedi-vim
" ------------------------------------------------------------------------

if g:jedi#auto_initialization
    setlocal omnifunc=jedi#complete

    " map ctrl+space for autocompletion
    if g:jedi#autocompletion_command == "<C-Space>"
        " in terminals, <C-Space> sometimes equals <Nul>
        inoremap <expr> <Nul> pumvisible() \|\| &omnifunc == '' ?
                \ "\<lt>C-n>" :
                \ "\<lt>C-x>\<lt>C-o><c-r>=pumvisible() ?" .
                \ "\"\\<lt>c-n>\\<lt>c-p>\\<lt>c-n>\" :" .
                \ "\" \\<lt>bs>\\<lt>C-n>\"\<CR>"
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
