if g:jedi#show_call_signatures == 1 && has('conceal')
  " conceal is normal for vim >= 7.3

  let e = g:jedi#call_signature_escape
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
  hi def link jediFat Pmenu
  hi def link jediFunction Pmenu

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
