if g:jedi#show_call_signatures > 0 && has('conceal')
    " conceal is normal for vim >= 7.3
 
    let s:e = g:jedi#call_signature_escape
    let s:l1 = s:e.'jedi=[^'.s:e.']*'.s:e.'[^'.s:e.']*'.s:e.'jedi'.s:e
    let s:l2 = s:e.'jedi=\?[^'.s:e.']*'.s:e
    exe 'syn match jediIgnore "'.s:l2.'" contained conceal'
    setlocal conceallevel=2
    syn match jediFatSymbol "*" contained conceal
    syn match jediFat "\*[^*]\+\*" contained contains=jediFatSymbol
    syn match jediSpace "\v[ ]+( )@=" contained
    exe 'syn match jediFunction "'.s:l1.'" keepend extend contains=jediIgnore,jediFat,jediSpace'
    unlet! s:e s:l1 s:l2
 
    hi def link jediIgnore Ignore
    hi def link jediFatSymbol Ignore
    hi def link jediSpace Normal
 
    if exists('g:colors_name')
        hi def link jediFunction CursorLine
        hi def link jediFat TabLine
    else
        hi jediFunction term=NONE cterm=NONE ctermfg=6 guifg=Black gui=NONE ctermbg=0 guibg=Grey
        hi jediFat term=bold,underline cterm=bold,underline gui=bold,underline ctermbg=0 guibg=#555555
    end
 
    " override defaults (add jediFunction to contains)
    syn match pythonComment "#.*$" contains=pythonTodo,@Spell,jediFunction
    syn region pythonString
        \ start=+[uU]\=\z(['"]\)+ end="\z1" skip="\\\\\|\\\z1"
        \ contains=pythonEscape,@Spell,jediFunction
    syn region pythonString
        \ start=+[uU]\=\z('''\|"""\)+ end="\z1" keepend
        \ contains=pythonEscape,pythonSpaceError,pythonDoctest,@Spell,jediFunction
    syn region pythonRawString
        \ start=+[uU]\=[rR]\z(['"]\)+ end="\z1" skip="\\\\\|\\\z1"
        \ contains=@Spell,jediFunction
    syn region pythonRawString
        \ start=+[uU]\=[rR]\z('''\|"""\)+ end="\z1" keepend
        \ contains=pythonSpaceError,pythonDoctest,@Spell,jediFunction
endif
