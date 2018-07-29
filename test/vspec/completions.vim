let g:jedi#completions_command = 'X'
source plugin/jedi.vim

describe 'completions'
    before
        new
        set filetype=python
    end

    after
        " default
        let g:jedi#popup_select_first = 1
        bd!
    end

    it 'smart import'
        exec "normal ifrom os "
        Expect getline('.') == 'from os import '
    end

    it 'no smart import after space'
        exec "normal! ifrom os "
        exec "normal  a "
        Expect getline('.') == 'from os  '
    end

    it 'import'
        " X is the completion command
        normal oimporX
        Expect getline('.') == 'import'
        normal a subproX
        Expect getline('.') == 'import subprocess'
    end

    it 'exception'
        normal oIndentationErrX
        Expect getline('.') == 'IndentationError'
        normal a().filenaX
        Expect getline('.') == 'IndentationError().filename'
    end

    it 'multi complete'
        normal oImpXErrX()
        Expect getline('.') == 'ImportError()'
    end

    it 'cycling through entries popup_select_first=0'
        let g:jedi#popup_select_first = 0
        execute "normal oraise impX\<C-n>"
        " It looks like this is currently not working properly.
        "Expect getline('.') == 'raise ImportError'
    end

    it 'cycling through entries popup_select_first=1'
        execute "normal oraise impX\<C-n>"
        Expect getline('.') == 'raise ImportWarning'
    end

    it 'longest'
        " -longest completes the first one
        set completeopt -=longest
        execute "normal oraise baseX"
        Expect getline('.') == 'raise BaseException'
        set completeopt +=longest
    end

    it 'dot_open'
    end
end

" vim: et:ts=4:sw=4
