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
end
