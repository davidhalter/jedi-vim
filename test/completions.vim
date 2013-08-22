let g:jedi#completions_command = 'X'
source plugin/jedi.vim

describe 'completions'
    before
        new
        set filetype=python
    end

    after
        close!
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

    it 'typing'
        normal oraisX ImpXErrX()
        Expect getline('.') == 'raise ImportError()'
    end
end

" vim: et:ts=4:sw=4
