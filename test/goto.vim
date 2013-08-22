let mapleader = '\'
source plugin/jedi.vim

describe 'goto_simple'
    before
        new
        set filetype=python
        put =[
        \   'def a(): pass',
        \   'b = a',
        \   'c = b',
        \ ]
        normal! ggdd
        normal! G$
        Expect line('.') == 3
        Expect g:loaded_jedi == 1
    end

    after
        close!
    end

    it 'goto_definitions'
        echo &runtimepath
        silent normal \d
        Expect line('.') == 1
        "Expect col('.') == 5
    end

    it 'goto_assignments'
        silent normal \g
        Expect line('.') == 2
        Expect col('.') == 1

        " cursor before `=` means that it stays there.
        silent normal \g
        Expect line('.') == 2
        Expect col('.') == 1

        " going to the last line changes it.
        normal! $
        silent normal \g
        Expect line('.') == 1
        Expect col('.') == 5
    end
end

" vim: et:ts=4:sw=4
