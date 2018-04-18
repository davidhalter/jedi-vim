let mapleader = '\'
source plugin/jedi.vim
source test/_utils.vim

describe 'goto simple'
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
    end

    after
        bd!
    end

    it 'goto definitions'
        normal \d
        Expect line('.') == 1
        Expect col('.') == 5
    end

    it 'goto assignments'
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


describe 'goto with tabs'
    before
        set filetype=python
        let g:jedi#use_tabs_not_buffers = 1
    end

    after
        bd!
        bd!
    end

    it 'follow import'
        put = ['import subprocess', 'subprocess']
        silent normal G\g
        Expect getline('.') == 'import subprocess'
        Expect line('.') == 2
        Expect col('.') == 8

        silent normal G\d
        Expect CurrentBufferIsModule('subprocess') == 1
        Expect line('.') == 1
        Expect col('.') == 1
        Expect tabpagenr('$') == 2
        Expect winnr('$') == 1
        tabprevious
        Expect bufname('%') == ''
    end

    it 'multi definitions'
        " This used to behave differently. Now we don't have any real multi
        " definitions.

        " put = ['import tokenize']
        " silent normal G$\d
        " Expect CurrentBufferIsModule('tokenize') == 1
        " Expect CurrentBufferIsModule('token') == 0
        " execute "normal \<CR>"
        " Expect tabpagenr('$') == 2
        " Expect winnr('$') == 1
        " Expect CurrentBufferIsModule('token') == 1

        " bd
        " silent normal G$\d
        " execute "normal j\<CR>"
        " Expect tabpagenr('$') == 2
        " Expect winnr('$') == 1
        " Expect CurrentBufferIsModule('tokenize') == 1
    end
end


describe 'goto with buffers'
    before
        set filetype=python
        let g:jedi#use_tabs_not_buffers = 0
    end

    after
        bd!
        bd!
        set nohidden
    end

    it 'no new tabs'
        put = ['import os']
        normal G$
        call jedi#goto_assignments()
        PythonJedi jedi_vim.goto()
        Expect CurrentBufferIsModule('os') == 0
        " Without hidden, it's not possible to open a new buffer, when the old
        " one is not saved.
        set hidden
        call jedi#goto_assignments()
        Expect CurrentBufferIsModule('os') == 1
        Expect winnr('$') == 1
        Expect tabpagenr('$') == 1
        Expect line('.') == 1
        Expect col('.') == 1
    end

    it 'multi definitions'
        " set hidden
        " put = ['import tokenize']
        " silent normal G$\d
        " Expect CurrentBufferIsModule('tokenize') == 0
        " Expect CurrentBufferIsModule('token') == 0
        " execute "normal \<CR>"
        " Expect tabpagenr('$') == 1
        " Expect winnr('$') == 1
        " Expect CurrentBufferIsModule('token') == 1

        " bd
        " silent normal G$\d
        " execute "normal j\<CR>"
        " Expect tabpagenr('$') == 1
        " Expect winnr('$') == 1
        " Expect CurrentBufferIsModule('tokenize') == 1
    end
end



describe 'goto with splits'
    before
        set filetype=python
        let g:jedi#use_splits_not_buffers = 'left'
    end

    after
        bd!
        bd!
    end

    it 'follow import'
        put = ['import subprocess', 'subprocess']
        silent normal G\g
        Expect getline('.') == 'import subprocess'
        Expect line('.') == 2
        Expect col('.') == 8

        silent normal G\d
        Expect CurrentBufferIsModule('subprocess') == 1
        Expect line('.') == 1
        Expect col('.') == 1
        Expect winnr('$') == 2
        wincmd l
        Expect bufname('%') == ''
    end

end


describe 'goto wildignore'
    before
        set filetype=python
        set wildignore=*,with\ spaces,*.pyc
        set hidden
        let g:jedi#use_tag_stack = 1
        let g:jedi#use_tabs_not_buffers = 0
        " Need to use splits for code coverage in new_buffer()
        let g:jedi#use_splits_not_buffers = 1

        put = ['from subprocess import Popen', 'Popen']
        Expect CurrentBufferIsModule('subprocess') == 0
        silent normal G
    end

    after
        bd!
        bd!
        set wildignore&vim
    end

    it 'restores wildignore'
        let before = &wildignore
        call jedi#goto()
        Expect getline('.') =~ 'Popen'
        Expect &wildignore == before
    end

    it 'not using tagstack'
        let g:jedi#use_tag_stack = 0
        call jedi#goto()
        Expect CurrentBufferIsModule('subprocess') == 1
        Expect getline('.') =~ 'Popen'
    end
end


" vim: et:ts=4:sw=4
