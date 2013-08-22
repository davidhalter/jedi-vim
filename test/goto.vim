describe 'goto_simple'
    before
        new
        put =[
        \   'def a(): pass',
        \   'b = a',
        \   'c = b',
        \ ]
        normal! G$
        Expect line('.') == 3
    end

    after
        close!
    end

    it 'goto_definitions'
        Expect range(1) == [0]
    end

    it 'goto_assignments'
        normal! <leader>g
        Expect line('.') == 2
        normal! $
        normal! <leader>g
        Expect line('.') == 1
    end
end

" vim: et:ts=4:sw=4
