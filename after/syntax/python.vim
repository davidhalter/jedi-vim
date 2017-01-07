if !jedi#init_python()
    finish
endif

call jedi#setup_call_signatures()

hi def jediUsage cterm=reverse gui=standout
