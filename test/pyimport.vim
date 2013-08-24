
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
        Expect tabpagenr('$') == 2
    end
end
