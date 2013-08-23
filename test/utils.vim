function! g:current_buffer_is_module(module_name)
    return g:ends_with(bufname('%'), a:module_name.'.py')
endfunction


function g:ends_with(string, end)
    let l:should = len(a:string) - strlen(a:end)
    return l:should == stridx(a:string, a:end, should)
endfunction

" vim: et:ts=4:sw=4
