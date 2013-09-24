if g:jedi#auto_initialization
    if g:jedi#completions_enabled
        " We need our own omnifunc, so this overrides the omnifunc set by
        " $VIMRUNTIME/ftplugin/python.vim.
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
endif
