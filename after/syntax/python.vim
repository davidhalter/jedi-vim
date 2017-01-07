if !jedi#init_python()
    finish
endif

call jedi#configure_call_signatures()

hi def jediUsage cterm=reverse gui=standout
