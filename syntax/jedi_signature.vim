setlocal concealcursor=nvic

hi def link jediCallsigNormal Normal

let e = g:jedi#call_signature_escape
let full = e.'jedi='.e.'.\{-}'.e.'jedi'.e
let ignore = e.'jedi=\='.e
exe 'syn match jediIgnore "'.ignore.'" contained conceal'
setlocal conceallevel=2
syn match jediFatSymbol "\*_\*" contained conceal
syn match jediFat "\*_\*.\{-}\*_\*" contained contains=jediFatSymbol
syn match jediSpace "\v[ ]+( )@=" contained
exe 'syn match jediFunction "'.full.'" keepend extend '
            \ .' contains=jediIgnore,jediFat,jediSpace'
            \ .' containedin=pythonComment,pythonString,pythonRawString'

hi def link jediIgnore Ignore
hi def link jediFatSymbol Ignore
hi def link jediSpace Normal

if hlexists('CursorLine')
    hi def link jediFunction CursorLine
else
    hi def jediFunction term=NONE cterm=NONE ctermfg=6 guifg=Black gui=NONE ctermbg=0 guibg=Grey
endif
if hlexists('TabLine')
    hi def link jediFat TabLine
else
    hi def jediFat term=bold,underline cterm=bold,underline gui=bold,underline ctermbg=0 guibg=#555555
endif
