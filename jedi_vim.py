"""
The Python parts of the Jedi library for VIM. It is mostly about communicating
with VIM.
"""

import traceback  # for exception output
import re
import os
import sys
from shlex import split as shsplit
try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest  # Python 2


def no_jedi_warning():
    vim.command('echoerr "Please install Jedi if you want to use jedi_vim."')


def echo_highlight(msg):
    vim_command('echohl WarningMsg | echom "%s" | echohl None' % msg)


import vim
try:
    import jedi
except ImportError:
    no_jedi_warning()
    jedi = None
else:
    version = jedi.__version__
    if isinstance(version, str):
        # the normal use case, now.
        from jedi import utils
        version = utils.version_info()
    if version < (0, 7):
        echo_highlight('Please update your Jedi version, it is to old.')

is_py3 = sys.version_info[0] >= 3
if is_py3:
    unicode = str


def catch_and_print_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (Exception, vim.error):
            print(traceback.format_exc())
            return None
    return wrapper


def _check_jedi_availability(show_error=False):
    def func_receiver(func):
        def wrapper(*args, **kwargs):
            if jedi is None:
                if show_error:
                    no_jedi_warning()
                return
            else:
                return func(*args, **kwargs)
        return wrapper
    return func_receiver


class VimError(Exception):
    def __init__(self, message, throwpoint, executing):
        super(type(self), self).__init__(message)
        self.throwpoint = throwpoint
        self.executing = executing

    def __str__(self):
        return self.message + '; created by: ' + repr(self.executing)


def _catch_exception(string, is_eval):
    """
    Interface between vim and python calls back to it.
    Necessary, because the exact error message is not given by `vim.error`.
    """
    e = 'jedi#_vim_exceptions(%s, %s)'
    result = vim.eval(e % (repr(PythonToVimStr(string, 'UTF-8')), is_eval))
    if 'exception' in result:
        raise VimError(result['exception'], result['throwpoint'], string)
    return result['result']


def vim_eval(string):
    return _catch_exception(string, 1)


def vim_command(string):
    _catch_exception(string, 0)


class PythonToVimStr(unicode):
    """ Vim has a different string implementation of single quotes """
    __slots__ = []

    def __new__(cls, obj, encoding='UTF-8'):
        if is_py3 or isinstance(obj, unicode):
            return unicode.__new__(cls, obj)
        else:
            return unicode.__new__(cls, obj, encoding)

    def __repr__(self):
        # this is totally stupid and makes no sense but vim/python unicode
        # support is pretty bad. don't ask how I came up with this... It just
        # works...
        # It seems to be related to that bug: http://bugs.python.org/issue5876
        if unicode is str:
            s = self
        else:
            s = self.encode('UTF-8')
        return '"%s"' % s.replace('\\', '\\\\').replace('"', r'\"')


@catch_and_print_exceptions
def get_script(source=None, column=None):
    jedi.settings.additional_dynamic_modules = \
        [b.name for b in vim.buffers if b.name is not None and b.name.endswith('.py')]
    if source is None:
        source = '\n'.join(vim.current.buffer)
    row = vim.current.window.cursor[0]
    if column is None:
        column = vim.current.window.cursor[1]
    buf_path = vim.current.buffer.name
    encoding = vim_eval('&encoding') or 'latin1'
    return jedi.Script(source, row, column, buf_path, encoding)


@_check_jedi_availability(show_error=False)
@catch_and_print_exceptions
def completions():
    row, column = vim.current.window.cursor
    # Clear call signatures in the buffer so they aren't seen by the completer.
    # Call signatures in the command line can stay.
    if vim_eval("g:jedi#show_call_signatures") == '1':
        clear_call_signatures()
    if vim.eval('a:findstart') == '1':
        count = 0
        for char in reversed(vim.current.line[:column]):
            if not re.match('[\w\d]', char):
                break
            count += 1
        vim.command('return %i' % (column - count))
    else:
        base = vim.eval('a:base')
        source = ''
        for i, line in enumerate(vim.current.buffer):
            # enter this path again, otherwise source would be incomplete
            if i == row - 1:
                source += line[:column] + base + line[column:]
            else:
                source += line
            source += '\n'
        # here again hacks, because jedi has a different interface than vim
        column += len(base)
        try:
            script = get_script(source=source, column=column)
            completions = script.completions()
            signatures = script.call_signatures()

            out = []
            for c in completions:
                d = dict(word=PythonToVimStr(c.name[:len(base)] + c.complete),
                         abbr=PythonToVimStr(c.name),
                         # stuff directly behind the completion
                         menu=PythonToVimStr(c.description),
                         info=PythonToVimStr(c.docstring()),  # docstr
                         icase=1,  # case insensitive
                         dup=1  # allow duplicates (maybe later remove this)
                         )
                out.append(d)

            strout = str(out)
        except Exception:
            # print to stdout, will be in :messages
            print(traceback.format_exc())
            strout = ''
            completions = []
            signatures = []

        show_call_signatures(signatures)
        vim.command('return ' + strout)


@_check_jedi_availability(show_error=True)
@catch_and_print_exceptions
def goto(is_definition=False, is_related_name=False, no_output=False):
    definitions = []
    script = get_script()
    try:
        if is_related_name:
            definitions = script.usages()
        elif is_definition:
            definitions = script.goto_definitions()
        else:
            definitions = script.goto_assignments()
    except jedi.NotFoundError:
        echo_highlight("Cannot follow nothing. Put your cursor on a valid name.")
    else:
        if no_output:
            return definitions
        if not definitions:
            echo_highlight("Couldn't find any definitions for this.")
        elif len(definitions) == 1 and not is_related_name:
            # just add some mark to add the current position to the jumplist.
            # this is ugly, because it overrides the mark for '`', so if anyone
            # has a better idea, let me know.
            vim_command('normal! m`')

            d = list(definitions)[0]
            if d.in_builtin_module():
                if d.is_keyword:
                    echo_highlight("Cannot get the definition of Python keywords.")
                else:
                    echo_highlight("Builtin modules cannot be displayed (%s)."
                                   % d.module_path)
            else:
                if d.module_path != vim.current.buffer.name:
                    result = new_buffer(d.module_path)
                    if not result:
                        return
                vim.current.window.cursor = d.line, d.column
        else:
            # multiple solutions
            lst = []
            for d in definitions:
                if d.in_builtin_module():
                    lst.append(dict(text=PythonToVimStr('Builtin ' + d.description)))
                else:
                    lst.append(dict(filename=PythonToVimStr(d.module_path),
                                    lnum=d.line, col=d.column + 1,
                                    text=PythonToVimStr(d.description)))
            vim_eval('setqflist(%s)' % repr(lst))
            vim_eval('jedi#add_goto_window(' + str(len(lst)) + ')')
    return definitions


@_check_jedi_availability(show_error=True)
@catch_and_print_exceptions
def show_documentation():
    script = get_script()
    try:
        definitions = script.goto_definitions()
    except jedi.NotFoundError:
        definitions = []
    except Exception:
        # print to stdout, will be in :messages
        definitions = []
        print("Exception, this shouldn't happen.")
        print(traceback.format_exc())

    if not definitions:
        echo_highlight('No documentation found for that.')
        vim.command('return')
    else:
        docs = ['Docstring for %s\n%s\n%s' % (d.desc_with_module, '=' * 40, d.docstring())
                if d.docstring() else '|No Docstring for %s|' % d for d in definitions]
        text = ('\n' + '-' * 79 + '\n').join(docs)
        vim.command('let l:doc = %s' % repr(PythonToVimStr(text)))
        vim.command('let l:doc_lines = %s' % len(text.split('\n')))
    return True


@catch_and_print_exceptions
def clear_call_signatures():
    # Check if using command line call signatures
    if vim_eval("g:jedi#show_call_signatures") == '2':
        vim_command('echo ""')
        return
    cursor = vim.current.window.cursor
    e = vim_eval('g:jedi#call_signature_escape')
    # We need two turns here to search and replace certain lines:
    # 1. Search for a line with a call signature and save the appended
    #    characters
    # 2. Actually replace the line and redo the status quo.
    py_regex = r'%sjedi=([0-9]+), (.*?)%s.*?%sjedi%s'.replace('%s', e)
    for i, line in enumerate(vim.current.buffer):
        match = re.search(r'%s' % py_regex, line)
        if match is not None:
            # Some signs were added to minimize syntax changes due to call
            # signatures. We have to remove them again. The number of them is
            # specified in `match.group(1)`.
            after = line[match.end() + int(match.group(1)):]
            line = line[:match.start()] + match.group(2) + after
            vim.current.buffer[i] = line
    vim.current.window.cursor = cursor


@_check_jedi_availability(show_error=False)
@catch_and_print_exceptions
def show_call_signatures(signatures=()):
    if vim_eval("has('conceal') && g:jedi#show_call_signatures") == '0':
        return

    if signatures == ():
        signatures = get_script().call_signatures()
    clear_call_signatures()

    if not signatures:
        return

    if vim_eval("g:jedi#show_call_signatures") == '2':
        return cmdline_call_signatures(signatures)

    for i, signature in enumerate(signatures):
        line, column = signature.bracket_start
        # signatures are listed above each other
        line_to_replace = line - i - 1
        # because there's a space before the bracket
        insert_column = column - 1
        if insert_column < 0 or line_to_replace <= 0:
            # Edge cases, when the call signature has no space on the screen.
            break

        # TODO check if completion menu is above or below
        line = vim_eval("getline(%s)" % line_to_replace)

        params = [p.description.replace('\n', '') for p in signature.params]
        try:
            # *_*PLACEHOLDER*_* makes something fat. See after/syntax file.
            params[signature.index] = '*_*%s*_*' % params[signature.index]
        except (IndexError, TypeError):
            pass

        # This stuff is reaaaaally a hack! I cannot stress enough, that
        # this is a stupid solution. But there is really no other yet.
        # There is no possibility in VIM to draw on the screen, but there
        # will be one (see :help todo Patch to access screen under Python.
        # (Marko Mahni, 2010 Jul 18))
        text = " (%s) " % ', '.join(params)
        text = ' ' * (insert_column - len(line)) + text
        end_column = insert_column + len(text) - 2  # -2 due to bold symbols

        # Need to decode it with utf8, because vim returns always a python 2
        # string even if it is unicode.
        e = vim_eval('g:jedi#call_signature_escape')
        if hasattr(e, 'decode'):
            e = e.decode('UTF-8')
        # replace line before with cursor
        regex = "xjedi=%sx%sxjedix".replace('x', e)

        prefix, replace = line[:insert_column], line[insert_column:end_column]

        # Check the replace stuff for strings, to append them
        # (don't want to break the syntax)
        regex_quotes = r'''\\*["']+'''
        # `add` are all the quotation marks.
        # join them with a space to avoid producing '''
        add = ' '.join(re.findall(regex_quotes, replace))
        # search backwards
        if add and replace[0] in ['"', "'"]:
            a = re.search(regex_quotes + '$', prefix)
            add = ('' if a is None else a.group(0)) + add

        tup = '%s, %s' % (len(add), replace)
        repl = prefix + (regex % (tup, text)) + add + line[end_column:]

        vim_eval('setline(%s, %s)' % (line_to_replace, repr(PythonToVimStr(repl))))


@catch_and_print_exceptions
def cmdline_call_signatures(signatures):
    def get_params(s):
        return [p.description.replace('\n', '') for p in s.params]

    if len(signatures) > 1:
        params = zip_longest(*map(get_params, signatures), fillvalue='_')
        params = ['(' + ', '.join(p) + ')' for p in params]
    else:
        params = get_params(signatures[0])
    text = ', '.join(params).replace('"', '\\"')

    # Allow 12 characters for ruler/showcmd - setting noruler/noshowcmd
    # here causes incorrect undo history
    max_msg_len = int(vim_eval('&columns')) - 12
    max_num_spaces = (max_msg_len - len(signatures[0].call_name)
                      - len(text) - 2)  # 2 accounts for parentheses
    if max_num_spaces < 0:
        return  # No room for the message
    _, column = signatures[0].bracket_start
    num_spaces = min(int(vim_eval('g:jedi#first_col +'
                     'wincol() - col(".")')) +
                     column - len(signatures[0].call_name),
                     max_num_spaces)
    spaces = ' ' * num_spaces

    try:
        index = [s.index for s in signatures if isinstance(s.index, int)][0]
        left = text.index(params[index])
        right = left + len(params[index])
        vim_command('                      echon "%s" | '
                    'echohl Function     | echon "%s" | '
                    'echohl None         | echon "("  | '
                    'echohl jediFunction | echon "%s" | '
                    'echohl jediFat      | echon "%s" | '
                    'echohl jediFunction | echon "%s" | '
                    'echohl None         | echon ")"'
                    % (spaces, signatures[0].call_name, text[:left],
                       text[left:right], text[right:]))
    except (TypeError, IndexError):
        vim_command('                      echon "%s" | '
                    'echohl Function     | echon "%s" | '
                    'echohl None         | echon "("  | '
                    'echohl jediFunction | echon "%s" | '
                    'echohl None         | echon ")"'
                    % (spaces, signatures[0].call_name, text))


@_check_jedi_availability(show_error=True)
@catch_and_print_exceptions
def rename():
    if not int(vim.eval('a:0')):
        _rename_cursor = vim.current.window.cursor

        vim_command('normal A ')  # otherwise startinsert doesn't work well
        vim.current.window.cursor = _rename_cursor

        vim_command('augroup jedi_rename')
        vim_command('autocmd InsertLeave <buffer> call jedi#rename(1)')
        vim_command('augroup END')

        vim_command('normal! diw')
        vim_command(':startinsert')
    else:
        window_path = vim.current.buffer.name
        # reset autocommand
        vim_command('autocmd! jedi_rename InsertLeave')

        replace = vim_eval("expand('<cword>')")
        vim_command('normal! u')  # undo new word
        cursor = vim.current.window.cursor
        vim_command('normal! u')  # undo the space at the end
        vim.current.window.cursor = cursor

        if replace is None:
            echo_highlight('No rename possible, if no name is given.')
        else:
            temp_rename = goto(is_related_name=True, no_output=True)
            # sort the whole thing reverse (positions at the end of the line
            # must be first, because they move the stuff before the position).
            temp_rename = sorted(temp_rename, reverse=True,
                                 key=lambda x: (x.module_path, x.start_pos))
            for r in temp_rename:
                if r.in_builtin_module():
                    continue

                if vim.current.buffer.name != r.module_path:
                    result = new_buffer(r.module_path)
                    if not result:
                        return

                vim.current.window.cursor = r.start_pos
                vim_command('normal! cw%s' % replace)

            result = new_buffer(window_path)
            if not result:
                return
            vim.current.window.cursor = cursor
            echo_highlight('Jedi did %s renames!' % len(temp_rename))


@_check_jedi_availability(show_error=True)
@catch_and_print_exceptions
def py_import():
    # args are the same as for the :edit command
    args = shsplit(vim.eval('a:args'))
    import_path = args.pop()
    text = 'import %s' % import_path
    scr = jedi.Script(text, 1, len(text), '')
    try:
        completion = scr.goto_assignments()[0]
    except IndexError:
        echo_highlight('Cannot find %s in sys.path!' % import_path)
    else:
        if completion.in_builtin_module():
            echo_highlight('%s is a builtin module.' % import_path)
        else:
            cmd_args = ' '.join([a.replace(' ', '\\ ') for a in args])
            new_buffer(completion.module_path, cmd_args)


@catch_and_print_exceptions
def py_import_completions():
    argl = vim.eval('a:argl')
    try:
        import jedi
    except ImportError:
        print('Pyimport completion requires jedi module: https://github.com/davidhalter/jedi')
        comps = []
    else:
        text = 'import %s' % argl
        script = jedi.Script(text, 1, len(text), '')
        comps = ['%s%s' % (argl, c.complete) for c in script.completions()]
    vim.command("return '%s'" % '\n'.join(comps))


@catch_and_print_exceptions
def new_buffer(path, options=''):
    # options are what you can to edit the edit options
    if vim_eval('g:jedi#use_tabs_not_buffers') == '1':
        _tabnew(path, options)
    elif not vim_eval('g:jedi#use_splits_not_buffers') == '1':
        user_split_option = vim_eval('g:jedi#use_splits_not_buffers')
        split_options = {
            'top': 'topleft split',
            'left': 'topleft vsplit',
            'right': 'botright vsplit',
            'bottom': 'botright split',
            'winwidth': 'vs'
        }
        if user_split_option == 'winwidth' and vim.current.window.width <= 2 * int(vim_eval("&textwidth ? &textwidth : 80")):
            split_options['winwidth'] = 'sp'
        if user_split_option not in split_options:
            print('g:jedi#use_splits_not_buffers value is not correct, valid options are: %s' % ','.join(split_options.keys()))
        else:
            vim_command(split_options[user_split_option] + " %s" % path)
    else:
        if vim_eval("!&hidden && &modified") == '1':
            if vim_eval("bufname('%')") is None:
                echo_highlight('Cannot open a new buffer, use `:set hidden` or save your buffer')
                return False
            else:
                vim_command('w')
        vim_command('edit %s %s' % (options, escape_file_path(path)))
    # sometimes syntax is being disabled and the filetype not set.
    if vim_eval('!exists("g:syntax_on")') == '1':
        vim_command('syntax enable')
    if vim_eval("&filetype != 'python'") == '1':
        vim_command('set filetype=python')
    return True


@catch_and_print_exceptions
def _tabnew(path, options=''):
    """
    Open a file in a new tab or switch to an existing one.

    :param options: `:tabnew` options, read vim help.
    """
    path = os.path.abspath(path)
    if vim_eval('has("gui")') == '1':
        vim_command('tab drop %s %s' % (options, escape_file_path(path)))
        return

    for tab_nr in range(int(vim_eval("tabpagenr('$')"))):
        for buf_nr in vim_eval("tabpagebuflist(%i + 1)" % tab_nr):
            buf_nr = int(buf_nr) - 1
            try:
                buf_path = vim.buffers[buf_nr].name
            except (LookupError, ValueError):
                # Just do good old asking for forgiveness.
                # don't know why this happens :-)
                pass
            else:
                if buf_path == path:
                    # tab exists, just switch to that tab
                    vim_command('tabfirst | tabnext %i' % (tab_nr + 1))
                    break
        else:
            continue
        break
    else:
        # tab doesn't exist, add a new one.
        vim_command('tabnew %s' % escape_file_path(path))


def escape_file_path(path):
    return path.replace(' ', r'\ ')


def print_to_stdout(level, str_out):
    print(str_out)
