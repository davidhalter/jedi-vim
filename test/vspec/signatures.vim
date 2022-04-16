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
        call jedi#show_call_signatures()
        Expect getline(3) == '?!?jedi=?!?   (*_*number*_*) ?!?jedi?!?'

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

    it 'simple with only parenthesis'
        noautocmd normal o
        noautocmd normal istaticmethod()
        call jedi#show_call_signatures()
        Expect getline(1) == '?!?jedi=?!?            (*_*f: Callable[..., Any]*_*) ?!?jedi?!?'
    end

    it 'highlights correct argument'
        noautocmd normal oformat(42, "x")
        " Move to x - highlights "x".
        noautocmd normal 2h
        call jedi#show_call_signatures()
        Expect getline(1) == '?!?jedi=?!?      (o: object, *_*format_spec: str=...*_*) ?!?jedi?!?'
        " Move left to 42 - highlights first argument ("value").
        noautocmd normal 4h
        call jedi#show_call_signatures()
        Expect getline(1) == '?!?jedi=?!?      (*_*o: object*_*, format_spec: str=...) ?!?jedi?!?'
    end

    it 'no signature'
        exe 'normal ostr '
        python3 jedi_vim.show_call_signatures()
        Expect getline(1, '$') == ['', 'str ']
    end

    it 'signatures disabled'
        call jedi#configure_call_signatures(0)

        exe 'normal ostr( '
        doautocmd CursorMoved
        Expect getline(1, '$') == ['', 'str( ']

        call jedi#configure_call_signatures(1)
    end

    it 'command line simple'
        let g:jedi#show_call_signatures = 2
        call jedi#configure_call_signatures()

        Expect exists('#CursorMoved') == 0

        exe 'normal ostaticmethod( '
        redir => msg
        call jedi#show_call_signatures()
        redir END
        Expect msg == "staticmethod(f: Callable[..., Any])"

        redir => msg
        doautocmd InsertLeave
        redir END
        Expect msg == "\n"

        normal Sdef foo(a, b): pass
        exe 'normal ofoo(a, b, c, '
        redir => msg
        call jedi#show_call_signatures()
        redir END
        Expect msg == "foo(a, b)"
    end

    it 'command line truncation'
        let g:jedi#show_call_signatures = 2
        call jedi#configure_call_signatures()

        function! Signature()
            redir => msg
            call jedi#show_call_signatures()
            redir END
            return msg
        endfunction

        let funcname = repeat('a', &columns - (30 + (&ruler ? 18 : 0)))
        put = 'def '.funcname.'(arg1, arg2, arg3, a, b, c):'
        put = '    pass'
        execute "normal o\<BS>".funcname."( "
        Expect Signature() == funcname."(arg1, …)"

        exe 'normal sarg1, '
        Expect Signature() == funcname."(…, arg2, …)"

        exe 'normal sarg2, arg3, '
        Expect Signature() == funcname."(…, a, b, c)"

        exe 'normal sa, b, '
        Expect Signature() == funcname."(…, c)"

        g/^/d
        put = 'def '.funcname.'('.repeat('b', 20).', arg2):'
        put = '    pass'
        execute "normal o\<BS>".funcname."( "
        Expect Signature() == funcname."(…)"
    end

    it 'command line no signature'
        let g:jedi#show_call_signatures = 2
        call jedi#configure_call_signatures()

        exe 'normal ostr '
        redir => msg
        call jedi#show_call_signatures()
        redir END
        Expect msg == ''
    end
end
