if g:jedi#show_function_definition == 1 && has('conceal')
  " conceal is normal for vim >= 7.3

  let e = g:jedi#function_definition_escape
  let l1 = e.'jedi=[^'.e.']*'.e.'[^'.e.']*'.e.'jedi'.e
  let l2 = e.'jedi=\?[^'.e.']*'.e
  exe 'syn match jediIgnore "'.l2.'" contained conceal'
  setlocal conceallevel=2
  syn match jediFatSymbol "*" contained conceal
  syn match jediFat "\*[^*]\+\*" contained contains=jediFatSymbol
  syn match jediSpace "\v[ ]+( )@=" contained
  exe 'syn match jediFunction "'.l1.'" keepend extend contains=jediIgnore,jediFat,jediSpace'

  hi def link jediIgnore Ignore
  hi def link jediFatSymbol Ignore
  hi def link jediSpace Normal
  hi jediFat term=bold,underline cterm=bold,underline gui=bold,underline ctermbg=0 guibg=#555555
  hi jediFunction term=NONE cterm=NONE ctermfg=6 guifg=Black gui=NONE ctermbg=0 guibg=Grey

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
