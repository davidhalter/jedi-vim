let mapleader = '\'
source plugin/jedi.vim
source test/utils.vim

describe 'goto_simple'
    before
        new  " open a new split
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

describe 'goto_with_new_tabs'
    before
        set filetype=python
    end

    after
        close!
        bd!
        bd!
    end

    it 'follow_import'
        put = ['import subprocess', 'subprocess']
        silent normal G\g
        Expect getline('.') == 'import subprocess'
        Expect line('.') == 2
        Expect col('.') == 8

        silent normal G\d
        Expect g:current_buffer_is_module('subprocess') == 1
        Expect line('.') == 1
        Expect col('.') == 1
        Expect tabpagenr('$') == 2
        tabprevious
        Expect bufname('%') == ''
    end
end

" vim: et:ts=4:sw=4
