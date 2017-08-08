"""Used in jedi-vim's jedi#debug_info()"""


def display_debug_info():
    import vim

    def echo(msg):
        vim.command('echo {0}'.format(msg))

    echo("printf(' - sys.version: `%s`', {0!r})".format(
        ', '.join([x.strip()
                   for x in __import__('sys').version.split('\n')])))
    echo("printf(' - site module: `%s`', {0!r})".format(
        __import__('site').__file__))

    try:
        import jedi_vim
    except Exception as e:
        echo("printf('ERROR: jedi_vim is not available: %s: %s', "
             "{0!r}, {1!r})".format(e.__class__.__name__, str(e)))
        return

    try:
        if jedi_vim.jedi is None:
            echo("'ERROR: could not import the \"jedi\" Python module.'")
            echo("printf('       The error was: %s', {0!r})".format(
                getattr(jedi_vim, "jedi_import_error", "UNKNOWN")))
        else:
            echo("printf('Jedi path: `%s`', {0!r})".format(
                jedi_vim.jedi.__file__))
            echo("printf(' - version: %s', {0!r})".format(
                jedi_vim.jedi.__version__))
            echo("' - sys_path:'")
            for p in jedi_vim.jedi.Script('')._evaluator.sys_path:
                echo("printf('    - `%s`', {0!r})".format(p))
    except Exception as e:
        echo("printf('There was an error accessing jedi_vim.jedi: %s', "
             "{0!r})".format(e))
