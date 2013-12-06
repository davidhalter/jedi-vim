if !has('python') && !has('python3')
    finish
endif
" ------------------------------------------------------------------------
" Initialization of jedi-vim
" ------------------------------------------------------------------------

function! s:init()
  if g:jedi#auto_initialization
      " goto / get_definition / usages
      if g:jedi#goto_assignments_command != ''
          for k in ['n', 'x']
              execute k."noremap <buffer> ".g:jedi#goto_assignments_command." :call jedi#goto_assignments()<CR>"
          endfor
      endif
      if g:jedi#goto_definitions_command != ''
          for k in ['n', 'x']
              execute k."noremap <buffer> ".g:jedi#goto_definitions_command." :call jedi#goto_definitions()<CR>"
          endfor
      endif
      if g:jedi#usages_command != ''
          for k in ['n', 'x']
              execute k."noremap <buffer> ".g:jedi#usages_command." :call jedi#usages()<CR>"
          endfor
      endif
      " rename
      if g:jedi#rename_command != ''
          for k in ['n', 'x']
              execute k."noremap <buffer> ".g:jedi#rename_command." :call jedi#rename()<CR>"
          endfor
      endif
      " documentation/pydoc
      if g:jedi#documentation_command != ''
          execute "nnoremap <silent> <buffer>".g:jedi#documentation_command." :call jedi#show_documentation()<CR>"
      endif

      if g:jedi#show_call_signatures == 1 && has('conceal')
          call jedi#configure_call_signatures()
      endif

      inoremap <silent> <buffer> . .<C-R>=jedi#complete_string(1)<CR>

      if g:jedi#auto_close_doc
          " close preview if its still open after insert
          autocmd InsertLeave <buffer> if pumvisible() == 0|pclose|endif
      end
  end

  if g:jedi#auto_vim_configuration
      setlocal completeopt=menuone,longest,preview
      if len(mapcheck('<C-c>', 'i')) == 0
          inoremap <C-c> <ESC>
      end
  end
endfunction

call s:init()
