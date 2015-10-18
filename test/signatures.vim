source plugin/jedi.vim

describe 'signatures'
    before
        set filetype=python
    end

    after
        bd!
        bd!
    end

    it 'simple'
        normal oabs( 
        " equals doautocmd CursorMovedI
        Python jedi_vim.show_call_signatures()

        Expect getline(1) == '=`=jedi=0, =`=   (*_*number*_*) =`=jedi=`='

        doautocmd InsertLeave 
        Expect getline(1) == ''
    end

    it 'no signature'
        normal ostr 
        Python jedi_vim.show_call_signatures()
        Expect getline(1, '$') == ['', 'str ']
    end

    it 'signatures disabled'
        let g:jedi#show_call_signatures = 0

        normal ostr( 
        Python jedi_vim.show_call_signatures()
        Expect getline(1, '$') == ['', 'str( ']

        let g:jedi#show_call_signatures = 1
    end

    it 'command line simple'
        let g:jedi#show_call_signatures = 2
        call jedi#configure_call_signatures()

        normal oabs( 
        redir => msg
        Python jedi_vim.show_call_signatures()
        redir END
        Expect msg == "\nabs(number)"

        redir => msg
        doautocmd InsertLeave 
        redir END
        Expect msg == "\n"
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

        let funcname = repeat('a', &columns - 30)
        put = 'def '.funcname.'(arg1, arg2, arg3, a, b, c):'
        put = '    pass'
        execute "normal o".funcname."( "
        Expect Signature() == "\n".funcname."(arg1, …)"

        normal sarg1, 
        Expect Signature() == "\n".funcname."(…, arg2, …)"

        normal sarg2, arg3, 
        Expect Signature() == "\n".funcname."(…, a, b, c)"

        normal sa, b, 
        Expect Signature() == "\n".funcname."(…, c)"

        g/^/d
        put = 'def '.funcname.'('.repeat('b', 20).', arg2):'
        put = '    pass'
        execute "normal o".funcname."( "
        Expect Signature() == "\n".funcname."(…)"
    end

    it 'command line no signature'
        let g:jedi#show_call_signatures = 2
        call jedi#configure_call_signatures()

        normal ostr 
        redir => msg
        Python jedi_vim.show_call_signatures()
        redir END
        Expect msg == "\n"
    end
end
