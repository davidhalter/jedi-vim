source plugin/jedi.vim

describe 'signatures'
    before
        enew
        set filetype=python
    end

    after
        try | %bwipeout! | catch | endtry
    end

    it 'simple'
        normal odef xyz(number): return
        normal o
        normal oxyz()
        doautocmd CursorHoldI
        Expect getline(3) == '?!?jedi=0, ?!?   (*_*number*_*) ?!?jedi?!?'

        doautocmd InsertLeave
        Expect getline(3) == ''
    end

    it 'multiple buffers'
        set hidden
        new
        setfiletype python
        redir => autocmds
        autocmd jedi_call_signatures * <buffer>
        redir END
        Expect autocmds =~# 'jedi_call_signatures'
        buffer #
        redir => autocmds
        autocmd jedi_call_signatures * <buffer>
        redir END
        Expect autocmds =~# 'jedi_call_signatures'
    end

    it 'simple after CursorHoldI with only parenthesis'
        noautocmd normal o
        doautocmd CursorHoldI
        noautocmd normal istaticmethod()
        doautocmd CursorHoldI
        Expect getline(1) == '?!?jedi=0, ?!?            (*_*f: Callable[..., Any]*_*) ?!?jedi?!?'
    end

    it 'highlights correct argument'
        if !has('python3')
          SKIP 'py2: no signatures with print()'
        endif
        noautocmd normal o
        doautocmd CursorHoldI
        noautocmd normal iprint(42, sep="X", )
        " Move to "=" - hightlights "sep=...".
        noautocmd normal 5h
        doautocmd CursorHoldI
        Expect getline(1) =~# '\V\^?!?jedi=0, ?!?     (*values: object, *_*sep: Optional[Text]=...*_*'
        " Move left to "=" - hightlights first argument ("values").
        " NOTE: it is arguable that maybe "sep=..." should be highlighted
        "       still, but this tests for the cache to be "busted", and that
        "       fresh results are retrieved from Jedi.
        noautocmd normal h
        doautocmd CursorHoldI
        Expect getline(1) =~# '\V\^?!?jedi=0, ?!?     (*_**values: object*_*, sep: Optional[Text]=...,'
    end

    it 'no signature'
        exe 'normal ostr '
        Python jedi_vim.show_call_signatures()
        Expect getline(1, '$') == ['', 'str ']
    end

    it 'signatures disabled'
        let g:jedi#show_call_signatures = 0

        exe 'normal ostr( '
        Python jedi_vim.show_call_signatures()
        Expect getline(1, '$') == ['', 'str( ']

        let g:jedi#show_call_signatures = 1
    end

    it 'command line simple'
        let g:jedi#show_call_signatures = 2
        call jedi#configure_call_signatures()

        exe 'normal ostaticmethod( '
        redir => msg
        Python jedi_vim.show_call_signatures()
        redir END
        Expect msg == "\nstaticmethod(f: Callable[..., Any])"

        redir => msg
        doautocmd InsertLeave
        redir END
        Expect msg == "\n"

        normal Sdef foo(a, b): pass
        exe 'normal ofoo(a, b, c, '
        redir => msg
        Python jedi_vim.show_call_signatures()
        redir END
        Expect msg == "\nfoo(a, b)"
    end

    it 'command line truncation'
        let g:jedi#show_call_signatures = 2
        call jedi#configure_call_signatures()

        function! Signature()
            redir => msg
            Python jedi_vim.show_call_signatures()
            redir END
            return msg
        endfunction

        let funcname = repeat('a', &columns - (30 + (&ruler ? 18 : 0)))
        put = 'def '.funcname.'(arg1, arg2, arg3, a, b, c):'
        put = '    pass'
        execute "normal o\<BS>".funcname."( "
        Expect Signature() == "\n".funcname."(arg1, …)"

        exe 'normal sarg1, '
        Expect Signature() == "\n".funcname."(…, arg2, …)"

        exe 'normal sarg2, arg3, '
        Expect Signature() == "\n".funcname."(…, a, b, c)"

        exe 'normal sa, b, '
        Expect Signature() == "\n".funcname."(…, c)"

        g/^/d
        put = 'def '.funcname.'('.repeat('b', 20).', arg2):'
        put = '    pass'
        execute "normal o\<BS>".funcname."( "
        Expect Signature() == "\n".funcname."(…)"
    end

    it 'command line no signature'
        let g:jedi#show_call_signatures = 2
        call jedi#configure_call_signatures()

        exe 'normal ostr '
        redir => msg
        Python jedi_vim.show_call_signatures()
        redir END
        Expect msg == "\n"
    end
end
