let g:jedi#completions_command = 'X'
source plugin/jedi.vim

describe 'completions'
    before
        new
        set filetype=python
    end

    it 'import'
        " X is the completion command
        normal oimporX
        Expect getline('.') == 'import'
        normal! a subproX
        Expect getline('.') == 'import subprocess'
    end
end

" vim: et:ts=4:sw=4
