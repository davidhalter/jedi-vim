"""
The Python parts of the Jedi library for VIM. It is mostly about communicating
with VIM.
"""

import traceback  # for exception output
import re
import os

import vim
import jedi
import jedi.keywords
from jedi._compatibility import unicode


def echo_highlight(msg):
    vim.command('echohl WarningMsg | echom "%s" | echohl None' % msg)


if not hasattr(jedi, '__version__') or jedi.__version__ < (0, 6, 0):
    echo_highlight('Please update your Jedi version, it is to old.')


class PythonToVimStr(unicode):
    """ Vim has a different string implementation of single quotes """
    __slots__ = []

    def __repr__(self):
        # this is totally stupid and makes no sense but vim/python unicode
        # support is pretty bad. don't ask how I came up with this... It just
        # works...
        # It seems to be related to that bug: http://bugs.python.org/issue5876
        s = self.encode('UTF-8')
        return '"%s"' % s.replace('\\', '\\\\').replace('"', r'\"')


def get_script(source=None, column=None):
    jedi.settings.additional_dynamic_modules = [b.name for b in vim.buffers
                            if b.name is not None and b.name.endswith('.py')]
    if source is None:
        source = '\n'.join(vim.current.buffer)
    row = vim.current.window.cursor[0]
    if column is None:
        column = vim.current.window.cursor[1]
    buf_path = vim.current.buffer.name
    encoding = vim.eval('&encoding') or 'latin1'
    return jedi.Script(source, row, column, buf_path, encoding)


def complete():
    row, column = vim.current.window.cursor
    clear_func_def()
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
            completions = script.complete()
            call_def = script.get_in_function_call()

            out = []
            for c in completions:
                d = dict(word=PythonToVimStr(c.word[:len(base)] + c.complete),
                         abbr=PythonToVimStr(c.word),
                         # stuff directly behind the completion
                         menu=PythonToVimStr(c.description),
                         info=PythonToVimStr(c.doc),  # docstr
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
            call_def = None

        #print 'end', strout
        show_func_def(call_def, len(completions))
        vim.command('return ' + strout)


def goto(is_definition=False, is_related_name=False, no_output=False):
    definitions = []
    script = get_script()
    try:
        if is_related_name:
            definitions = script.related_names()
        elif is_definition:
            definitions = script.get_definition()
        else:
            definitions = script.goto()
    except jedi.NotFoundError:
        echo_highlight(
                    "Cannot follow nothing. Put your cursor on a valid name.")
    except Exception:
        # print to stdout, will be in :messages
        echo_highlight("Some different eror, this shouldn't happen.")
        print(traceback.format_exc())
    else:
        if no_output:
            return definitions
        if not definitions:
            echo_highlight("Couldn't find any definitions for this.")
        elif len(definitions) == 1 and not is_related_name:
            # just add some mark to add the current position to the jumplist.
            # this is ugly, because it overrides the mark for '`', so if anyone
            # has a better idea, let me know.
            vim.command('normal! m`')

            d = list(definitions)[0]
            if d.in_builtin_module():
                if d.is_keyword:
                    echo_highlight(
                            "Cannot get the definition of Python keywords.")
                else:
                    echo_highlight("Builtin modules cannot be displayed.")
            else:
                if d.module_path != vim.current.buffer.name:
                    vim.eval('jedi#new_buffer(%s)' % \
                                        repr(PythonToVimStr(d.module_path)))
                vim.current.window.cursor = d.line_nr, d.column
                vim.command('normal! zt')  # cursor at top of screen
        else:
            # multiple solutions
            lst = []
            for d in definitions:
                if d.in_builtin_module():
                    lst.append(dict(text=
                                PythonToVimStr('Builtin ' + d.description)))
                else:
                    lst.append(dict(filename=PythonToVimStr(d.module_path),
                                    lnum=d.line_nr, col=d.column + 1,
                                    text=PythonToVimStr(d.description)))
            vim.eval('setqflist(%s)' % repr(lst))
            vim.eval('jedi#add_goto_window()')
    return definitions


def show_pydoc():
    script = get_script()
    try:
        definitions = script.get_definition()
    except jedi.NotFoundError:
        definitions = []
    except Exception:
        # print to stdout, will be in :messages
        definitions = []
        print("Exception, this shouldn't happen.")
        print(traceback.format_exc())

    if not definitions:
        vim.command('return')
    else:
        docs = ['Docstring for %s\n%s\n%s' % (d.desc_with_module, '='*40, d.doc) if d.doc
                    else '|No Docstring for %s|' % d for d in definitions]
        text = ('\n' + '-' * 79 + '\n').join(docs)
        vim.command('let l:doc = %s' % repr(PythonToVimStr(text)))
        vim.command('let l:doc_lines = %s' % len(text.split('\n')))


def clear_func_def():
    cursor = vim.current.window.cursor
    e = vim.eval('g:jedi#function_definition_escape')
    regex = r'%sjedi=([0-9]+), ([^%s]*)%s.*%sjedi%s'.replace('%s', e)
    for i, line in enumerate(vim.current.buffer):
        match = re.search(r'%s' % regex, line)
        if match is not None:
            vim_regex = r'\v' + regex.replace('=', r'\=') + '.{%s}' % \
                                                        int(match.group(1))
            vim.command(r'try | %s,%ss/%s/\2/g | catch | endtry' \
                                                % (i + 1, i + 1, vim_regex))
            vim.eval('histdel("search", -1)')
            vim.command('let @/ = histget("search", -1)')
    vim.current.window.cursor = cursor


def show_func_def(call_def=None, completion_lines=0):
    if vim.eval("has('conceal') && g:jedi#show_function_definition") == '0':
        return
    try:
        if call_def == None:
            call_def = get_script().get_in_function_call()
        clear_func_def()

        if call_def is None:
            return

        row, column = call_def.bracket_start
        if column < 2 or row == 0:
            return  # edge cases, just ignore

        # TODO check if completion menu is above or below
        row_to_replace = row - 1
        line = vim.eval("getline(%s)" % row_to_replace)

        insert_column = column - 2  # because it has stuff at the beginning

        params = [p.get_code().replace('\n', '') for p in call_def.params]
        try:
            params[call_def.index] = '*%s*' % params[call_def.index]
        except (IndexError, TypeError):
            pass

        # This stuff is reaaaaally a hack! I cannot stress enough, that this is
        # a stupid solution. But there is really no other yet. There is no
        # possibility in VIM to draw on the screen, but there will be one (see
        # :help todo Patch to access screen under Python. (Marko Mahni, 2010
        # Jul 18))
        text = " (%s) " % ', '.join(params)
        text = ' ' * (insert_column - len(line)) + text
        end_column = insert_column + len(text) - 2  # -2 due to bold symbols

        # Need to decode it with utf8, because vim returns always a python 2
        # string even if it is unicode.
        e = vim.eval('g:jedi#function_definition_escape').decode('UTF-8')
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

        vim.eval('setline(%s, %s)' % \
                            (row_to_replace, repr(PythonToVimStr(repl))))
    except Exception:
        print(traceback.format_exc())


def rename():
    if not int(vim.eval('a:0')):
        _rename_cursor = vim.current.window.cursor

        vim.command('normal A ')  # otherwise startinsert doesn't work well
        vim.current.window.cursor = _rename_cursor

        vim.command('augroup jedi_rename')
        vim.command('autocmd InsertLeave <buffer> call jedi#rename(1)')
        vim.command('augroup END')

        vim.command('normal! diw')
        vim.command(':startinsert')
    else:
        window_path = vim.current.buffer.name
        # reset autocommand
        vim.command('autocmd! jedi_rename InsertLeave')

        replace = vim.eval("expand('<cword>')")
        vim.command('normal! u')  # undo new word
        cursor = vim.current.window.cursor
        vim.command('normal! u')  # undo the space at the end
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
                    vim.eval("jedi#new_buffer('%s')" % r.module_path)

                vim.current.window.cursor = r.start_pos
                vim.command('normal! cw%s' % replace)

            vim.eval("jedi#new_buffer('%s')" % window_path)
            vim.current.window.cursor = cursor
            echo_highlight('Jedi did %s renames!' % len(temp_rename))


def tabnew(path):
    "Open a file in a new tab or switch to an existing one"
    path = os.path.abspath(path)
    if vim.eval('has("gui")') == '1':
        vim.command('tab drop %s' % path)
        return

    for tab_nr in range(int(vim.eval("tabpagenr('$')"))):
        for buf_nr in vim.eval("tabpagebuflist(%i + 1)" % tab_nr):
            buf_nr = int(buf_nr) - 1
            try:
                buf_path = vim.buffers[buf_nr].name
            except IndexError:
                # Just do good old asking for forgiveness.
                # don't know why this happens :-)
                pass
            else:
                if buf_path == path:
                    # tab exists, just switch to that tab
                    vim.command('tabfirst | tabnext %i' % (tab_nr + 1))
                    break
        else:
            continue
        break
    else:
        # tab doesn't exist, add a new one.
        vim.command('tabnew %s' % path)


def escape_file_path(path):
    return path.replace(' ', r'\ ')


def print_to_stdout(level, str_out):
    print(str_out)
