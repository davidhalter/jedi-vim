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
        normal ostr( 
        " equals doautocmd CursorMovedI
        Python jedi_vim.show_call_signatures()

        Expect getline(1) == '≡jedi=0, ≡   (*obj*) ≡jedi≡'

        doautocmd InsertLeave 
        Expect getline(1) == ''
    end

    it 'no signature'
        normal ostr 
        Python jedi_vim.show_call_signatures()
        Expect getline(1, '$') == ['', 'str ']
    end

    it 'signatures disabled'
        let g:jedi#show_signatures = 0

        normal ostr( 
        Python jedi_vim.show_call_signatures()
        Expect getline(1, '$') == ['', 'str( ']

        let g:jedi#show_signatures = 1
    end
end
