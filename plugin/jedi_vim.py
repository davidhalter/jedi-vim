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

temp_rename = None  # used for jedi#rename


class PythonToVimStr(str):
    """ Vim has a different string implementation of single quotes """
    __slots__ = []

    def __repr__(self):
        return '"%s"' % self.replace('\\', '\\\\').replace('"', r'\"')


def echo_highlight(msg):
    vim.command('echohl WarningMsg | echo "%s" | echohl None' % msg)


def get_script(source=None, column=None):
    jedi.settings.additional_dynamic_modules = [b.name for b in vim.buffers
                            if b.name is not None and b.name.endswith('.py')]
    if source is None:
        source = '\n'.join(vim.current.buffer)
    row = vim.current.window.cursor[0]
    if column is None:
        column = vim.current.window.cursor[1]
    buf_path = vim.current.buffer.name
    return jedi.Script(source, row, column, buf_path)


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
                d = dict(word=c.word[:len(base)] + c.complete,
                         abbr=c.word,
                         # stuff directly behind the completion
                         menu=PythonToVimStr(c.description),
                         info=PythonToVimStr(c.doc),  # docstr
                         icase=1,  # case insensitive
                         dup=1  # allow duplicates (maybe later remove this)
                )
                out.append(d)

            out.sort(key=lambda x: x['word'].lower())

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
                if isinstance(d.definition, jedi.keywords.Keyword):
                    echo_highlight(
                            "Cannot get the definition of Python keywords.")
                else:
                    echo_highlight("Builtin modules cannot be displayed.")
            else:
                if d.module_path != vim.current.buffer.name:
                    vim.eval('jedi#new_buffer(%s)' % repr(d.module_path))
                vim.current.window.cursor = d.line_nr, d.column
                vim.command('normal! zt')  # cursor at top of screen
        else:
            # multiple solutions
            lst = []
            for d in definitions:
                if d.in_builtin_module():
                    lst.append(dict(text='Builtin ' + d.description))
                else:
                    lst.append(dict(filename=d.module_path, lnum=d.line_nr,
                                        col=d.column + 1, text=d.description))
            vim.eval('setqflist(%s)' % str(lst))
            vim.eval('<sid>add_goto_window()')
    return definitions


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
        # replace line before with cursor
        e = vim.eval('g:jedi#function_definition_escape')
        regex = "xjedi=%sx%sxjedix".replace('x', e)

        prefix, replace = line[:insert_column], line[insert_column:end_column]

        # Check the replace stuff for strings, to append them
        # (don't want to break the syntax)
        regex_quotes = r'''\\*["']+'''
        # `add` are all the quotation marks.
        add = ''.join(re.findall(regex_quotes, replace))
        # search backwards
        if add and replace[0] in ['"', "'"]:
            a = re.search(regex_quotes + '$', prefix)
            add = ('' if a is None else a.group(0)) + add

        tup = '%s, %s' % (len(add), replace)
        repl = ("%s" + regex + "%s") % \
                                (prefix, tup, text, add + line[end_column:])

        vim.eval('setline(%s, %s)' % \
                            (row_to_replace, repr(PythonToVimStr(repl))))
    except Exception:
        print(traceback.format_exc())


def rename():
    global temp_rename
    if not int(vim.eval('a:0')):
        temp_rename = goto(is_related_name=True, no_output=True)
        _rename_cursor = vim.current.window.cursor

        vim.command('normal A ')  # otherwise startinsert doesn't work well
        vim.current.window.cursor = _rename_cursor

        vim.command('augroup jedi_rename')
        vim.command('autocmd InsertLeave <buffer> call jedi#rename(1)')
        vim.command('augroup END')

        vim.command('normal! diw')
        vim.command(':startinsert')
    else:
        cursor = vim.current.window.cursor
        window_path = vim.current.buffer.name
        # reset autocommand
        vim.command('autocmd! jedi_rename InsertLeave')

        replace = vim.eval("expand('<cword>')")
        vim.command('normal! u')  # undo new word
        vim.command('normal! u')  # 2u didn't work...

        if replace is None:
            echo_highlight('No rename possible, if no name is given.')
        else:
            for r in temp_rename:
                if r.in_builtin_module():
                    continue
                if vim.current.buffer.name != r.module_path:
                    vim.eval("jedi#new_buffer('%s')" % r.module_path)

                vim.current.window.cursor = r.start_pos
                vim.command('normal! cw%s' % replace)

            vim.current.window.cursor = cursor
            vim.eval("jedi#new_buffer('%s')" % window_path)
            echo_highlight('Jedi did %s renames!' % len(temp_rename))
        # reset rename variables
        temp_rename = None


def tabnew(path):
    path = os.path.abspath(path)
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
