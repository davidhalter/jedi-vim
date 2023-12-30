function! health#jedi#check() abort
  call v:lua.vim.health.start('jedi')
  silent call jedi#debug_info()
endfunction
