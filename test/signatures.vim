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
        Python jedi_vim.show_call_signatures()

        "doautocmd CursorMovedI

        Expect getline(1) == 'a'

        "doautocmd InsertLeave 
    end
end
