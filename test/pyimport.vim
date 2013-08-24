source plugin/jedi.vim
source test/utils.vim

describe 'pyimport'
    after
        bd!
        bd!
    end

    it 'open_tab'
        Pyimport os 
        Expect g:current_buffer_is_module('os') == 1
        Pyimport subprocess 
        Expect g:current_buffer_is_module('subprocess') == 1
        " the empty tab is sometimes also a tab
        Expect tabpagenr('$') >= 2
    end

    it 'completion'
        " don't know how to test this.
        "execute "Pyimport subproc\<Tab>"
        "Expect g:current_buffer_is_module('subprocess') == 1
    end
end
