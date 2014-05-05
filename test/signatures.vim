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

        Expect getline(1) == '≡jedi=0, ≡   (*number*) ≡jedi≡'

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
end
