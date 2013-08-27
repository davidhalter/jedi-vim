source plugin/jedi.vim

describe 'documentation_docstrings'
    before
        set filetype=python
    end

    it 'simple'
        put = 'ImportError'
        normal GK
        Expect bufname('%') == "'__doc__'"
        Expect &filetype == 'rst'
        let content = join(getline(1,'$'), "\n")
        Expect stridx(content, "Import can't find module") > 0
        normal K
        Expect bufname('%') == ''
    end
end

" vim: et:ts=4:sw=4
