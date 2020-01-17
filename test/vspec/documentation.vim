source plugin/jedi.vim

describe 'documentation docstrings'
    before
        set filetype=python
    end

    after
        try | %bwipeout! | catch | endtry
    end

    it 'simple'
        Expect maparg('K') == ':call jedi#show_documentation()<CR>'
        put = 'ImportError'
        normal GK
        Expect bufname('%') == "__doc__"
        Expect &filetype == 'rst'
        let header = getline(1, 2)
        PythonJedi vim.vars["is_py2"] = sys.version_info[0] == 2
        if g:is_py2
            Expect header[0] == "Docstring for __builtin__:class ImportError"
            Expect header[1] == "==========================================="
        else
            Expect header[0] == "Docstring for builtins:class ImportError"
            Expect header[1] == "========================================"
        endif
        let content = join(getline(3, '$'), "\n")
        Expect stridx(content, "Import can't find module") > 0
        normal K
        Expect bufname('%') == ''
    end

    it 'no documentation'
        put = 'x = 2'
        normal o<ESC>GK
        Expect bufname('%') == ''
    end
end

" vim: et:ts=4:sw=4
