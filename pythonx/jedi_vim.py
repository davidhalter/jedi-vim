# -*- coding: utf-8 -*-
"""
The Python parts of the Jedi library for VIM. It is mostly about communicating
with VIM.
"""

from typing import Optional
import traceback  # for exception output
import re
import os
import sys
from shlex import split as shsplit
from contextlib import contextmanager
from pathlib import Path
try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest  # Python 2

import vim

is_py3 = sys.version_info[0] >= 3
if is_py3:
    ELLIPSIS = "…"
    unicode = str
else:
    ELLIPSIS = u"…"

IS_NVIM = hasattr(vim, 'from_nvim')


_show_call_signatures_mode = None
"""Current mode for call signatures (1: concealing, 2: command line, 3: floatwin)"""


try:
    # Somehow sys.prefix is set in combination with VIM and virtualenvs.
    # However the sys path is not affected. Just reset it to the normal value.
    sys.prefix = sys.base_prefix
    sys.exec_prefix = sys.base_exec_prefix
except AttributeError:
    # If we're not in a virtualenv we don't care. Everything is fine.
    pass


class PythonToVimStr(unicode):
    """ Vim has a different string implementation of single quotes """
    __slots__ = []

    def __new__(cls, obj, encoding='UTF-8'):
        if not (is_py3 or isinstance(obj, unicode)):
            obj = unicode.__new__(cls, obj, encoding)

        # Vim cannot deal with zero bytes:
        obj = obj.replace('\0', '\\0')
        return unicode.__new__(cls, obj)

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


class VimError(Exception):
    def __init__(self, message, throwpoint, executing):
        super(type(self), self).__init__(message)
        self.message = message
        self.throwpoint = throwpoint
        self.executing = executing

    def __str__(self):
        return "{}; created by {!r} (in {})".format(
            self.message, self.executing, self.throwpoint
        )


def _catch_exception(string, is_eval):
    """
    Interface between vim and python calls back to it.
    Necessary, because the exact error message is not given by `vim.error`.
    """
    result = vim.eval('jedi#_vim_exceptions({0}, {1})'.format(
        repr(PythonToVimStr(string, 'UTF-8')), int(is_eval)))
    if 'exception' in result:
        raise VimError(result['exception'], result['throwpoint'], string)
    return result['result']


def vim_command(string):
    _catch_exception(string, is_eval=False)


def vim_eval(string):
    return _catch_exception(string, is_eval=True)


def no_jedi_warning(error=None):
    vim.command('echohl WarningMsg')
    vim.command('echom "Please install Jedi if you want to use jedi-vim."')
    if error:
        vim.command('echom "The error was: {0}"'.format(error))
    vim.command('echohl None')


def echo_highlight(msg):
    vim_command('echohl WarningMsg | echom "jedi-vim: {0}" | echohl None'.format(
        str(msg).replace('"', '\\"')))


jedi_path = os.path.join(os.path.dirname(__file__), 'jedi')
sys.path.insert(0, jedi_path)
parso_path = os.path.join(os.path.dirname(__file__), 'parso')
sys.path.insert(0, parso_path)

try:
    import jedi
except ImportError:
    jedi = None
    jedi_import_error = sys.exc_info()
else:
    try:
        version = jedi.__version__
    except Exception as e:  # e.g. AttributeError
        echo_highlight(
            "Error when loading the jedi python module ({0}). "
            "Please ensure that Jedi is installed correctly (see Installation "
            "in the README.".format(e))
        jedi = None
    else:
        if isinstance(version, str):
            # the normal use case, now.
            from jedi import utils
            version = utils.version_info()
        if version < (0, 7):
            echo_highlight('Please update your Jedi version, it is too old.')
finally:
    sys.path.remove(jedi_path)
    sys.path.remove(parso_path)


class VimCompat:
    _eval_cache = {}
    _func_cache = {}

    @classmethod
    def has(cls, what):
        try:
            return cls._eval_cache[what]
        except KeyError:
            ret = cls._eval_cache[what] = cls.call('has', what)
            return ret

    @classmethod
    def call(cls, func, *args):
        try:
            f = cls._func_cache[func]
        except KeyError:
            if IS_NVIM:
                f = cls._func_cache[func] = getattr(vim.funcs, func)
            else:
                f = cls._func_cache[func] = vim.Function(func)
        return f(*args)

    @classmethod
    def setqflist(cls, items, title, context):
        if cls.has('patch-7.4.2200'):  # can set qf title.
            what = {'title': title}
            if cls.has('patch-8.0.0590'):  # can set qf context
                what['context'] = {'jedi_usages': context}
            if cls.has('patch-8.0.0657'):  # can set items via "what".
                what['items'] = items
                cls.call('setqflist', [], ' ', what)
            else:
                # Can set title (and maybe context), but needs two calls.
                cls.call('setqflist', items)
                cls.call('setqflist', items, 'a', what)
        else:
            cls.call('setqflist', items)

    @classmethod
    def setqflist_title(cls, title):
        if cls.has('patch-7.4.2200'):
            cls.call('setqflist', [], 'a', {'title': title})

    @classmethod
    def can_update_current_qflist_for_context(cls, context):
        if cls.has('patch-8.0.0590'):  # can set qf context
            return cls.call('getqflist', {'context': 1})['context'] == {
                'jedi_usages': context,
            }


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


# Tuple of cache key / project
_current_project_cache = None, None


def get_project():
    try:
        vim_environment_path = vim_eval("b:jedi_environment_path")
    except VimError:
        vim_environment_path = ""

    if vim_environment_path in ("", None):
        vim_environment_path = vim_eval("g:jedi#environment_path")
    vim_project_path = vim_eval("g:jedi#project_path")
    vim_added_sys_path = vim_eval("g:jedi#added_sys_path")

    global _current_project_cache
    cache_key = dict(project_path=vim_project_path, environment_path=vim_environment_path)
    if cache_key == _current_project_cache[0]:
        return _current_project_cache[1]

    if vim_environment_path in ("auto", "", None):
        environment_path = None
    else:
        environment_path = vim_environment_path

    if vim_project_path in ("auto", "", None):
        project_path = jedi.get_default_project().path
    else:
        project_path = vim_project_path

    project = jedi.Project(project_path,
                           environment_path=environment_path,
                           added_sys_path=vim_added_sys_path)

    _current_project_cache = cache_key, project
    return project


@catch_and_print_exceptions
def choose_environment():
    args = shsplit(vim.eval('a:args'))

    envs = list(jedi.find_system_environments())
    envs.extend(jedi.find_virtualenvs(paths=args or None))

    env_paths = [env.executable for env in envs]

    vim_command('belowright new')
    vim.current.buffer[:] = env_paths
    vim.current.buffer.name = "Hit Enter to Choose an Environment"
    vim_command(
        'setlocal buftype=nofile bufhidden=wipe noswapfile nobuflisted readonly nomodifiable')
    vim_command('noremap <buffer> <ESC> :bw<CR>')
    vim_command('noremap <buffer> <CR> :python3 jedi_vim.choose_environment_hit_enter()<CR>')


@catch_and_print_exceptions
def choose_environment_hit_enter():
    vim.vars['jedi#environment_path'] = vim.current.line
    vim_command('bd')


@catch_and_print_exceptions
def load_project():
    path = vim.eval('a:args')
    vim.vars['jedi#project_path'] = path
    env_path = vim_eval("g:jedi#environment_path")
    if env_path == 'auto':
        env_path = None
    if path:
        try:
            project = jedi.Project.load(path)
        except FileNotFoundError:
            project = jedi.Project(path, environment_path=env_path)
            project.save()
    else:
        project = jedi.get_default_project()
        path = project.path
        project.save()

    global _current_project_cache
    cache_key = dict(project_path=path, environment_path=env_path)
    _current_project_cache = cache_key, project


@catch_and_print_exceptions
def get_script(source=None):
    jedi.settings.additional_dynamic_modules = [
        b.name for b in vim.buffers if (
            b.name is not None and
            b.name.endswith('.py') and
            b.options['buflisted'])]
    if source is None:
        source = '\n'.join(vim.current.buffer)
    buf_path = vim.current.buffer.name
    if not buf_path:
        # If a buffer has no name its name is an empty string.
        buf_path = None

    return jedi.Script(source, path=buf_path, project=get_project())


def get_pos(column=None):
    row = vim.current.window.cursor[0]
    if column is None:
        column = vim.current.window.cursor[1]
    return row, column


@_check_jedi_availability(show_error=False)
@catch_and_print_exceptions
def completions():
    row, column = vim.current.window.cursor
    if vim.eval('a:findstart') == '1':
        count = 0
        for char in reversed(vim.current.line[:column]):
            if not re.match(r'[\w\d]', char):
                break
            count += 1
        vim.command('return %i' % (column - count))
        return

    # Clear call signatures in the buffer so they aren't seen by the completer.
    if _show_call_signatures_mode == 1:
        restore_signatures = clear_call_signatures(temporary=True)
    else:
        restore_signatures = None

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
        script = get_script(source=source)
        completions = script.complete(*get_pos(column))

        add_info = "preview" in vim.eval("&completeopt").split(",")
        out = []
        for c in completions:
            d = dict(word=PythonToVimStr(c.name[:len(base)] + c.complete),
                     abbr=PythonToVimStr(c.name_with_symbols),
                     # stuff directly behind the completion
                     menu=PythonToVimStr(c.description),
                     icase=1,  # case insensitive
                     dup=1  # allow duplicates (maybe later remove this)
                     )
            if add_info:
                try:
                    d["info"] = PythonToVimStr(c.docstring())
                except Exception:
                    print("jedi-vim: error with docstring for %r: %s" % (
                        c, traceback.format_exc()))
            out.append(d)

        strout = str(out)
    except Exception:
        # print to stdout, will be in :messages
        print(traceback.format_exc())
        strout = ''
        completions = []

    if restore_signatures:
        show_call_signatures()
    vim.command('return ' + strout)


@contextmanager
def tempfile(content):
    # Using this instead of the tempfile module because Windows won't read
    # from a file not yet written to disk
    with open(vim_eval('tempname()'), 'w') as f:
        f.write(content)
    try:
        yield f
    finally:
        os.unlink(f.name)


@_check_jedi_availability(show_error=True)
@catch_and_print_exceptions
def goto(mode="goto"):
    """
    :param str mode: "definition", "assignment", "goto"
    :rtype: list of jedi.api.classes.Name
    """
    script = get_script()
    pos = get_pos()
    if mode == "goto":
        names = script.goto(*pos, follow_imports=True)
    elif mode == "definition":
        names = script.infer(*pos)
    elif mode == "assignment":
        names = script.goto(*pos)
    elif mode == "stubs":
        names = script.goto(*pos, follow_imports=True, only_stubs=True)

    if not names:
        echo_highlight("Couldn't find any definitions for this.")
    elif len(names) == 1 and mode != "related_name":
        n = list(names)[0]
        _goto_specific_name(n)
    else:
        show_goto_multi_results(names, mode)
    return names


def _goto_specific_name(n, options=''):
    if n.column is None:
        if n.is_keyword:
            echo_highlight("Cannot get the definition of Python keywords.")
        else:
            name = 'Namespaces' if n.type == 'namespace' else 'Builtin modules'
            echo_highlight(
                "%s cannot be displayed (%s)."
                % (name, n.full_name or n.name)
            )
    else:
        using_tagstack = int(vim_eval('g:jedi#use_tag_stack')) == 1
        result = set_buffer(n.module_path, options=options,
                            using_tagstack=using_tagstack)
        if not result:
            return []
        if (using_tagstack and n.module_path and
                n.module_path.exists()):
            tagname = n.name
            with tempfile('{0}\t{1}\t{2}'.format(
                    tagname, n.module_path, 'call cursor({0}, {1})'.format(
                        n.line, n.column + 1))) as f:
                old_tags = vim.eval('&tags')
                old_wildignore = vim.eval('&wildignore')
                try:
                    # Clear wildignore to ensure tag file isn't ignored
                    vim.command('set wildignore=')
                    vim.command('let &tags = %s' %
                                repr(PythonToVimStr(f.name)))
                    vim.command('tjump %s' % tagname)
                finally:
                    vim.command('let &tags = %s' %
                                repr(PythonToVimStr(old_tags)))
                    vim.command('let &wildignore = %s' %
                                repr(PythonToVimStr(old_wildignore)))
        vim.current.window.cursor = n.line, n.column


def relpath(path):
    """Make path relative to cwd if it is below."""
    abspath = os.path.abspath(path)
    if abspath.startswith(os.getcwd()):
        return os.path.relpath(path)
    return path


def annotate_description(n):
    code = n.get_line_code().strip()
    if n.type == 'statement':
        return code
    if n.type == 'function':
        if code.startswith('def'):
            return code
        typ = 'def'
    else:
        typ = n.type
    return '[%s] %s' % (typ, code)


def show_goto_multi_results(names, mode):
    """Create (or reuse) a quickfix list for multiple names."""
    global _current_names

    lst = []
    (row, col) = vim.current.window.cursor
    current_idx = None
    current_def = None
    for n in names:
        if n.column is None:
            # Typically a namespace, in the future maybe other things as
            # well.
            lst.append(dict(text=PythonToVimStr(n.description)))
        else:
            text = annotate_description(n)
            lst.append(dict(filename=PythonToVimStr(relpath(str(n.module_path))),
                            lnum=n.line, col=n.column + 1,
                            text=PythonToVimStr(text)))

            # Select current/nearest entry via :cc later.
            if n.line == row and n.column <= col:
                if (current_idx is None
                        or (abs(lst[current_idx]["col"] - col)
                            > abs(n.column - col))):
                    current_idx = len(lst)
                    current_def = n

    # Build qflist title.
    qf_title = mode
    if current_def is not None:
        if current_def.full_name:
            qf_title += ": " + current_def.full_name
        else:
            qf_title += ": " + str(current_def)
        select_entry = current_idx
    else:
        select_entry = 0

    qf_context = id(names)
    if (_current_names
            and VimCompat.can_update_current_qflist_for_context(qf_context)):
        # Same list, only adjust title/selected entry.
        VimCompat.setqflist_title(qf_title)
        vim_command('%dcc' % select_entry)
    else:
        VimCompat.setqflist(lst, title=qf_title, context=qf_context)
        for_usages = mode == "usages"
        vim_eval('jedi#add_goto_window(%d, %d)' % (for_usages, len(lst)))
        vim_command('%d' % select_entry)


def _same_names(a, b):
    """Compare without _inference_state.

    Ref: https://github.com/davidhalter/jedi-vim/issues/952)
    """
    return all(
        x._name.start_pos == y._name.start_pos
        and x.module_path == y.module_path
        and x.name == y.name
        for x, y in zip(a, b)
    )


@catch_and_print_exceptions
def usages(visuals=True):
    script = get_script()
    names = script.get_references(*get_pos())
    if not names:
        echo_highlight("No usages found here.")
        return names

    if visuals:
        global _current_names

        if _current_names:
            if _same_names(_current_names, names):
                names = _current_names
            else:
                clear_usages()
                assert not _current_names

        show_goto_multi_results(names, "usages")
        if not _current_names:
            _current_names = names
            highlight_usages()
        else:
            assert names is _current_names  # updated above
    return names


_current_names = None
"""Current definitions to use for highlighting."""
_pending_names = {}
"""Pending definitions for unloaded buffers."""
_placed_names_in_buffers = set()
"""Set of buffers for faster cleanup."""


IS_NVIM = hasattr(vim, 'from_nvim')
if IS_NVIM:
    vim_prop_add = None
else:
    vim_prop_type_added = False
    try:
        vim_prop_add = vim.Function("prop_add")
    except ValueError:
        vim_prop_add = None
    else:
        vim_prop_remove = vim.Function("prop_remove")


def clear_usages():
    """Clear existing highlights."""
    global _current_names
    if _current_names is None:
        return
    _current_names = None

    if IS_NVIM:
        for buf in _placed_names_in_buffers:
            src_ids = buf.vars.get('_jedi_usages_src_ids')
            if src_ids is not None:
                for src_id in src_ids:
                    buf.clear_highlight(src_id)
    elif vim_prop_add:
        for buf in _placed_names_in_buffers:
            vim_prop_remove({
                'type': 'jediUsage',
                'all': 1,
                'bufnr': buf.number,
            })
    else:
        # Unset current window only.
        assert _current_names is None
        highlight_usages_for_vim_win()

    _placed_names_in_buffers.clear()


def highlight_usages():
    """Set usage names to be highlighted.

    With Neovim it will use the nvim_buf_add_highlight API to highlight all
    buffers already.

    With Vim without support for text-properties only the current window is
    highlighted via matchaddpos, and autocommands are setup to highlight other
    windows on demand.  Otherwise Vim's text-properties are used.
    """
    global _current_names, _pending_names

    names = _current_names
    _pending_names = {}

    if IS_NVIM or vim_prop_add:
        bufs = {x.name: x for x in vim.buffers}
        defs_per_buf = {}
        for name in names:
            try:
                buf = bufs[str(name.module_path)]
            except KeyError:
                continue
            defs_per_buf.setdefault(buf, []).append(name)

        if IS_NVIM:
            # We need to remember highlight ids with Neovim's API.
            buf_src_ids = {}
            for buf, names in defs_per_buf.items():
                buf_src_ids[buf] = []
                for name in names:
                    src_id = _add_highlighted_name(buf, name)
                    buf_src_ids[buf].append(src_id)
            for buf, src_ids in buf_src_ids.items():
                buf.vars['_jedi_usages_src_ids'] = src_ids
        else:
            for buf, names in defs_per_buf.items():
                try:
                    for name in names:
                        _add_highlighted_name(buf, name)
                except vim.error as exc:
                    if exc.args[0].startswith('Vim:E275:'):
                        # "Cannot add text property to unloaded buffer"
                        _pending_names.setdefault(buf.name, []).extend(
                            names)
    else:
        highlight_usages_for_vim_win()


def _handle_pending_usages_for_buf():
    """Add (pending) highlights for the current buffer (Vim with textprops)."""
    buf = vim.current.buffer
    bufname = buf.name
    try:
        buf_names = _pending_names[bufname]
    except KeyError:
        return
    for name in buf_names:
        _add_highlighted_name(buf, name)
    del _pending_names[bufname]


def _add_highlighted_name(buf, name):
    lnum = name.line
    start_col = name.column

    # Skip highlighting of module definitions that point to the start
    # of the file.
    if name.type == 'module' and lnum == 1 and start_col == 0:
        return

    _placed_names_in_buffers.add(buf)

    # TODO: validate that name.name is at this position?
    # Would skip the module definitions from above already.

    length = len(name.name)
    if vim_prop_add:
        # XXX: needs jediUsage highlight (via after/syntax/python.vim).
        global vim_prop_type_added
        if not vim_prop_type_added:
            vim.eval("prop_type_add('jediUsage', {'highlight': 'jediUsage'})")
            vim_prop_type_added = True
        vim_prop_add(lnum, start_col+1, {
            'type': 'jediUsage',
            'bufnr': buf.number,
            'length': length,
        })
        return

    assert IS_NVIM
    end_col = name.column + length
    src_id = buf.add_highlight('jediUsage', lnum-1, start_col, end_col,
                               src_id=0)
    return src_id


def highlight_usages_for_vim_win():
    """Highlight usages in the current window.

    It stores the matchids in a window-local variable.

    (matchaddpos() only works for the current window.)
    """
    win = vim.current.window

    cur_matchids = win.vars.get('_jedi_usages_vim_matchids')
    if cur_matchids:
        if cur_matchids[0] == vim.current.buffer.number:
            return

        # Need to clear non-matching highlights.
        for matchid in cur_matchids[1:]:
            expr = 'matchdelete(%d)' % int(matchid)
            vim.eval(expr)

    matchids = []
    if _current_names:
        buffer_path = vim.current.buffer.name
        for name in _current_names:
            if (str(name.module_path) or '') == buffer_path:
                positions = [
                    [name.line,
                     name.column + 1,
                     len(name.name)]
                ]
                expr = "matchaddpos('jediUsage', %s)" % repr(positions)
                matchids.append(int(vim_eval(expr)))

    if matchids:
        vim.current.window.vars['_jedi_usages_vim_matchids'] = [
            vim.current.buffer.number] + matchids
    elif cur_matchids is not None:
        # Always set it (uses an empty list for "unset", which is not possible
        # using del).
        vim.current.window.vars['_jedi_usages_vim_matchids'] = []

    # Remember if clearing is needed for later buffer autocommands.
    vim.current.buffer.vars['_jedi_usages_needs_clear'] = bool(matchids)


@_check_jedi_availability(show_error=True)
@catch_and_print_exceptions
def show_documentation():
    script = get_script()
    try:
        names = script.help(*get_pos())
    except Exception:
        # print to stdout, will be in :messages
        names = []
        print("Exception, this shouldn't happen.")
        print(traceback.format_exc())

    if not names:
        echo_highlight('No documentation found for that.')
        vim.command('return')
        return

    docs = []
    for n in names:
        doc = n.docstring()
        if doc:
            title = 'Docstring for %s %s' % (n.type, n.full_name or n.name)
            underline = '=' * len(title)
            docs.append('%s\n%s\n%s' % (title, underline, doc))
        else:
            docs.append('|No Docstring for %s|' % n)
        text = ('\n' + '-' * 79 + '\n').join(docs)
        vim.command('let l:doc = %s' % repr(PythonToVimStr(text)))
        vim.command('let l:doc_lines = %s' % len(text.split('\n')))
    return True


@catch_and_print_exceptions
def clear_call_signatures(temporary=False):
    if _show_call_signatures_mode == 2:
        vim_command('echo ""')
        return

    if _show_call_signatures_mode == 3:
        if IS_NVIM:
            win = vim.current.buffer.vars.get('_jedi_signature_window')
            if win:
                vim.api.win_close(win, True)
                del vim.current.buffer.vars['_jedi_signature_window']
        else:
            try:
                winid = vim.current.buffer.vars['_jedi_signature_winid']
            except KeyError:
                pass
            else:
                popup_hide = vim.Function("popup_hide")
                popup_hide(winid)
        return

    r = False
    orig_lines = vim.current.buffer.vars.get('_jedi_callsig_orig', {})
    if orig_lines:
        orig_modified = int(vim_eval("&modified"))

        for linenr, line in orig_lines.items():
            # Check that the line would be reset, helps with keeping a single
            # undochain.
            # assert line != vim.current.buffer[int(linenr)-1]
            if line != vim.current.buffer[int(linenr)-1]:
                vim.current.buffer[int(linenr)-1] = line
                vim_command('let b:_jedi_changing_text = changenr()')
                r = True
        if not orig_modified:
            vim_command('set nomodified')
        if not temporary:
            vim_command('unlet b:_jedi_callsig_orig')
    return r


@_check_jedi_availability(show_error=False)
@catch_and_print_exceptions
def show_call_signatures(signatures=(), mode=None):
    """Show call signatures and remember current mode.

    Passing in the mode from Vim avoids to call back into it several times.
    """
    global _show_call_signatures_mode
    if mode is None and _show_call_signatures_mode is None:
        raise Exception('jedi-vim: called show_call_signatures without mode')
    _show_call_signatures_mode = mode

    # We need to clear the signatures before we calculate them again. The
    # reason for this is that call signatures are unfortunately written to the
    # buffer.
    if _show_call_signatures_mode != 2:
        clear_call_signatures()
    if signatures == ():
        signatures = get_script().get_signatures(*get_pos())

    if not signatures:
        return

    if mode == 2:
        return cmdline_call_signatures(signatures)

    if mode == 3:
        return call_signatures_floatwin(signatures)

    return call_signatures_inline(signatures)


@catch_and_print_exceptions
def call_signatures_inline(signatures):
    set_lines = []
    seen_sigs = []
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

        # Descriptions are usually looking like `param name`, remove the param.
        params = [p.description.replace('\n', '').replace('param ', '', 1)
                  for p in signature.params]
        try:
            # *_*PLACEHOLDER*_* makes something fat via jediFatSymbol.
            params[signature.index] = '*_*%s*_*' % params[signature.index]
        except (IndexError, TypeError):
            pass

        # Skip duplicates.
        if params in seen_sigs:
            continue
        seen_sigs.append(params)

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
        regex = "xjedi=x{}xjedix".replace('x', e)

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

        repl = prefix + regex.format(text) + add + line[end_column:]

        set_lines.append((line_to_replace, repl))

    if not set_lines:
        return

    orig_modified = int(vim_eval("&modified"))
    orig_lines = {}
    for linenr, line in set_lines:
        orig_lines[str(linenr)] = vim.current.buffer[linenr-1]
        vim_command('silent! undojoin')
        vim.current.buffer[int(linenr)-1] = line
    vim.current.buffer.vars['_jedi_callsig_orig'] = orig_lines
    if not orig_modified:
        vim_command('set nomodified')


@catch_and_print_exceptions
def call_signatures_floatwin(signatures):
    """Display signatures using Neovim's floating / Vim's popup window."""
    seen_sigs = []
    sig_bracket_start_col = None
    sig_bracket_start_row = None
    lines = []
    max_visible_sig_width = 0

    # Build text lines from signatures.
    # This has quite some common code copied from call_signatures_inline still.
    # TODO: refactor?
    for i, signature in enumerate(signatures):
        row, column = signature.bracket_start
        if sig_bracket_start_col:
            assert row == sig_bracket_start_row
            assert column == sig_bracket_start_col
        sig_bracket_start_row = row
        sig_bracket_start_col = column

        # Descriptions are usually looking like `param name`, remove the param.
        # Also replace leading params with ellipsis (for shortness).
        params = [p.description.replace('\n', '').replace('param ', '', 1)
                  if idx >= signature.index
                  else "…"
                  for idx, p in enumerate(signature.params)]

        # Get (visible) width without any added concealed text.
        w = len("(%s)" % ', '.join(params))
        if w > max_visible_sig_width:
            max_visible_sig_width = w
        try:
            # *_*PLACEHOLDER*_* makes something fat via jediFatSymbol.
            params[signature.index] = '*_*%s*_*' % params[signature.index]
        except (IndexError, TypeError):
            pass

        # Skip duplicates.
        if params in seen_sigs:
            continue
        seen_sigs.append(params)

        text = "(%s)" % ', '.join(params)

        # Need to decode it with utf8, because vim returns always a python 2
        # string even if it is unicode.
        e = vim_eval('g:jedi#call_signature_escape')
        if hasattr(e, 'decode'):
            e = e.decode('UTF-8')
        # replace line before with cursor
        regex = "xjedi=x{}xjedix".replace('x', e)
        text = regex.format(text)
        lines.append(text)

    cur_cursor = vim.current.window.cursor
    cur_row = cur_cursor[0]
    sig_row_offset = sig_bracket_start_row - cur_row
    if sig_row_offset == 0:
        # Display above when on current line.
        sig_row_offset = -1
    else:
        # Display above when anything after signatures parenthesis (for
        # multiline statements.
        sig_buffer_line = vim.current.buffer[sig_bracket_start_row-1]
        if len(sig_buffer_line) > sig_bracket_start_col + 1:
            sig_row_offset -= 1
    cur_col = cur_cursor[1]
    floatwin_col_offset = sig_bracket_start_col - cur_col

    height = len(lines)

    # Display above/below when at the top/bottom of the window.
    # It limits "height" to the available room, preferring the other for
    # when there is more room.
    wline = VimCompat.call('winline')
    floatwin_row_offset = None

    space_above = wline - (cur_row - sig_bracket_start_row) - 1
    space_below = VimCompat.call("winheight", 0) - wline

    if space_above <= 0 and space_below <= 0:
        # No space above sig_bracket_start_row and cur_row, display it at the
        # top of the window.
        floatwin_row_offset = 1 - wline
    else:
        # Check if there is only whitespace for where the signature would be put
        # above, and prefer to putting it below otherwise (since often code is used
        # rather from above than below (and should not be covered therefore)).
        # TODO: might prefer above/below via setting in general, and/or for when
        #       the signature/function definition spans multiple lines (but AFAICS
        #       that info is not available (would need signature.bracket_end?)
        prefer_below = False
        for lnum_offset_above in range(1, height + 1):
            lnum_above = sig_bracket_start_row - lnum_offset_above
            if len(VimCompat.call('getline', lnum_above).rstrip()) > sig_bracket_start_col - 1:
                prefer_below = True
                break

        put_below = prefer_below
        if prefer_below:
            if height > space_below and space_above > space_below:
                put_below = False
        else:
            if height > space_above and space_below > space_above:
                put_below = True

        if put_below:
            floatwin_row_offset = 1
            height = min(space_below, height)
        else:
            height = min(space_above, height)
            floatwin_row_offset = sig_row_offset - height

    if IS_NVIM:
        buf = vim.current.buffer.vars.get('_jedi_signature_buffer')
        if not buf:
            buf = vim.api.create_buf(False, True)
            vim.current.buffer.vars['_jedi_signature_buffer'] = buf

        vim.api.buf_set_lines(buf, 0, -1, True, lines)

        # Use maximum width to not have Nvim move it left.
        # https://github.com/neovim/neovim/issues/10811
        win_screen_col_start = vim.funcs.getwininfo(vim.funcs.win_getid())[0]["wincol"]
        win_screen_col_cur = win_screen_col_start + vim.funcs.wincol()
        start_wincol = win_screen_col_cur + floatwin_col_offset
        max_width = vim.options["columns"] - start_wincol + 1
        width = min([max_visible_sig_width, max_width])

        opts = {
            'relative': 'cursor',
            'width': width,
            'height': height,
            'col': floatwin_col_offset,
            'row': floatwin_row_offset,
            'anchor': 'NW',
            'style': 'minimal',
        }
        win = vim.api.open_win(buf, 0, opts)
        vim.api.buf_set_option(buf, 'syntax', 'jedi_signature')

        vim.current.buffer.vars['_jedi_signature_window'] = win

    else:
        line = ("%d" if floatwin_row_offset < 0 else "+%d") % floatwin_row_offset
        col = ("%d" if floatwin_col_offset < 0 else "+%d") % floatwin_col_offset

        popup_opts = vim.Dictionary(**{
            "line": "cursor%s" % line,
            "col": "cursor%s" % col,
            "pos": "topleft",
            "wrap": 0,
            "fixed": 1,
            "flip": 1,
            "minwidth": max_visible_sig_width,
            "maxwidth": max_visible_sig_width,
            "maxheight": height,
        })

        try:
            winid = vim.current.buffer.vars['_jedi_signature_winid']
        except KeyError:
            popup_create = vim.Function("popup_create")
            winid = popup_create(lines, popup_opts)
            buf = int(vim.eval("winbufnr(%d)" % winid))

            vim.command("call setwinvar(%d, '&wincolor', 'jediCallsigNormal')" % winid)

            # Set syntax to apply concealing.
            vim.eval("win_execute(%d, 'set syntax=jedi_signature')" % winid)

            # vim.eval("setbufvar(%d, '&filetype', 'jedi_signature')" % buf)
            # # vim.eval("win_execute(%d, 'doautocmd FileType')" % winid)
            # vim.eval("setwinvar(%d, '&concealcursor', 'nvic')" % (winid,))
            # vim.eval("setwinvar(%d, '&conceallevel', 2)" % (winid,))

            vim.current.buffer.vars['_jedi_signature_winid'] = winid
        else:
            popup_settext = vim.Function("popup_settext")
            popup_settext(winid, lines)
            popup_move = vim.Function("popup_move")
            popup_move(winid, popup_opts)
            popup_show = vim.Function("popup_show")
            popup_show(winid)


@catch_and_print_exceptions
def cmdline_call_signatures(signatures):
    def get_params(s):
        return [p.description.replace('\n', '').replace('param ', '', 1) for p in s.params]

    def escape(string):
        return string.replace('"', '\\"').replace(r'\n', r'\\n')

    def join():
        return ', '.join(filter(None, (left, center, right)))

    def too_long():
        return len(join()) > max_msg_len

    if len(signatures) > 1:
        params = zip_longest(*map(get_params, signatures), fillvalue='_')
        params = ['(' + ', '.join(p) + ')' for p in params]
    else:
        params = get_params(signatures[0])

    index = next(iter(s.index for s in signatures if s.index is not None), None)

    # Allow 12 characters for showcmd plus 18 for ruler - setting
    # noruler/noshowcmd here causes incorrect undo history
    max_msg_len = int(vim_eval('&columns')) - 12
    if int(vim_eval('&ruler')):
        max_msg_len -= 18
    max_msg_len -= len(signatures[0].name) + 2  # call name + parentheses

    if max_msg_len < (1 if params else 0):
        return
    elif index is None:
        text = escape(', '.join(params))
        if params and len(text) > max_msg_len:
            text = ELLIPSIS
    elif max_msg_len < len(ELLIPSIS):
        return
    else:
        left = escape(', '.join(params[:index]))
        center = escape(params[index])
        right = escape(', '.join(params[index + 1:]))
        while too_long():
            if left and left != ELLIPSIS:
                left = ELLIPSIS
                continue
            if right and right != ELLIPSIS:
                right = ELLIPSIS
                continue
            if (left or right) and center != ELLIPSIS:
                left = right = None
                center = ELLIPSIS
                continue
            if too_long():
                # Should never reach here
                return

    max_num_spaces = max_msg_len
    if index is not None:
        max_num_spaces -= len(join())
    _, column = signatures[0].bracket_start
    spaces = min(int(vim_eval('s:callsig_cmd_first_col +'
                              'wincol() - col(".")')) +
                 column - len(signatures[0].name),
                 max_num_spaces) * ' '

    if index is not None:
        vim_command('                      echon "%s" | '
                    'echohl Function     | echon "%s" | '
                    'echohl None         | echon "("  | '
                    'echohl jediFunction | echon "%s" | '
                    'echohl jediFat      | echon "%s" | '
                    'echohl jediFunction | echon "%s" | '
                    'echohl None         | echon ")"'
                    % (spaces, signatures[0].name,
                       left + ', ' if left else '',
                       center, ', ' + right if right else ''))
    else:
        vim_command('                      echon "%s" | '
                    'echohl Function     | echon "%s" | '
                    'echohl None         | echon "(%s)"'
                    % (spaces, signatures[0].name, text))


@_check_jedi_availability(show_error=True)
@catch_and_print_exceptions
def rename():
    if not int(vim.eval('a:0')):
        # Need to save the cursor position before insert mode
        cursor = vim.current.window.cursor
        changenr = vim.eval('changenr()')  # track undo tree
        vim_command('augroup jedi_rename')
        vim_command('autocmd InsertLeave <buffer> call jedi#rename'
                    '({}, {}, {})'.format(cursor[0], cursor[1], changenr))
        vim_command('augroup END')

        vim_command("let s:jedi_replace_orig = expand('<cword>')")
        line = vim_eval('getline(".")')
        vim_command('normal! diw')
        if re.match(r'\w+$', line[cursor[1]:]):
            # In case the deleted word is at the end of the line we need to
            # move the cursor to the end.
            vim_command('startinsert!')
        else:
            vim_command('startinsert')

    else:
        # Remove autocommand.
        vim_command('autocmd! jedi_rename InsertLeave')

        args = vim.eval('a:000')
        cursor = tuple(int(x) for x in args[:2])
        changenr = args[2]

        # Get replacement, if there is something on the cursor.
        # This won't be the case when the user ends insert mode right away,
        # and `<cword>` would pick up the nearest word instead.
        if vim_eval('getline(".")[getpos(".")[2]-1]') != ' ':
            replace = vim_eval("expand('<cword>')")
        else:
            replace = None

        vim_command('undo {}'.format(changenr))

        vim.current.window.cursor = cursor

        if replace:
            return do_rename(replace)


def rename_visual():
    replace = vim.eval('input("Rename to: ")')
    orig = vim.eval('getline(".")[(getpos("\'<")[2]-1):getpos("\'>")[2]]')
    do_rename(replace, orig)


def do_rename(replace, orig=None):
    if not len(replace):
        echo_highlight('No rename possible without name.')
        return

    if orig is None:
        orig = vim_eval('s:jedi_replace_orig')

    # Save original window / tab.
    saved_tab = int(vim_eval('tabpagenr()'))
    saved_win = int(vim_eval('winnr()'))

    temp_rename = usages(visuals=False)
    # Sort the whole thing reverse (positions at the end of the line
    # must be first, because they move the stuff before the position).
    temp_rename = sorted(temp_rename, reverse=True,
                         key=lambda x: (str(x.module_path), x.line, x.column))
    buffers = set()
    for r in temp_rename:
        if r.in_builtin_module():
            continue

        result = set_buffer(r.module_path)
        if not result:
            echo_highlight('Failed to create buffer window for %s!' % (r.module_path))
            continue

        buffers.add(vim.current.buffer.name)

        # Replace original word.
        r_line = vim.current.buffer[r.line - 1]
        vim.current.buffer[r.line - 1] = (r_line[:r.column] + replace +
                                          r_line[r.column + len(orig):])

    # Restore previous tab and window.
    vim_command('tabnext {0:d}'.format(saved_tab))
    vim_command('{0:d}wincmd w'.format(saved_win))

    if len(buffers) > 1:
        echo_highlight('Jedi did {0:d} renames in {1:d} buffers!'.format(
            len(temp_rename), len(buffers)))
    else:
        echo_highlight('Jedi did {0:d} renames!'.format(len(temp_rename)))


@_check_jedi_availability(show_error=True)
@catch_and_print_exceptions
def py_import():
    args = shsplit(vim.eval('a:args'))
    import_path = args.pop()
    name = next(get_project().search(import_path), None)
    if name is None:
        echo_highlight('Cannot find %s in your project or on sys.path!' % import_path)
    else:
        cmd_args = ' '.join([a.replace(' ', '\\ ') for a in args])
        _goto_specific_name(name, options=cmd_args)


@catch_and_print_exceptions
def py_import_completions():
    argl = vim.eval('a:argl')
    if jedi is None:
        print('Pyimport completion requires jedi module: https://github.com/davidhalter/jedi')
        comps = []
    else:
        names = get_project().complete_search(argl)
        comps = [argl + n for n in sorted(set(c.complete for c in names))]
    vim.command("return '%s'" % '\n'.join(comps))


@catch_and_print_exceptions
def set_buffer(path: Optional[Path], options='', using_tagstack=False):
    """
    Opens a new buffer if we have to or does nothing. Returns True in case of
    success.
    """
    path = str(path or '')
    # Check both, because it might be an empty string
    if path in (vim.current.buffer.name, os.path.abspath(vim.current.buffer.name)):
        return True

    path = relpath(path)
    # options are what you can to edit the edit options
    if int(vim_eval('g:jedi#use_tabs_not_buffers')) == 1:
        _tabnew(path, options)
    elif not vim_eval('g:jedi#use_splits_not_buffers') in [1, '1']:
        user_split_option = vim_eval('g:jedi#use_splits_not_buffers')
        split_options = {
            'top': 'topleft split',
            'left': 'topleft vsplit',
            'right': 'botright vsplit',
            'bottom': 'botright split',
            'winwidth': 'vs'
        }
        if (user_split_option == 'winwidth' and
                vim.current.window.width <= 2 * int(vim_eval(
                    "&textwidth ? &textwidth : 80"))):
            split_options['winwidth'] = 'sp'
        if user_split_option not in split_options:
            print('Unsupported value for g:jedi#use_splits_not_buffers: {0}. '
                  'Valid options are: {1}.'.format(
                      user_split_option, ', '.join(split_options.keys())))
        else:
            vim_command(split_options[user_split_option] + " %s" % escape_file_path(path))
    else:
        if int(vim_eval("!&hidden && &modified")) == 1:
            if not vim_eval("bufname('%')"):
                echo_highlight('Cannot open a new buffer, use `:set hidden` or save your buffer')
                return False
            else:
                vim_command('w')
        if using_tagstack:
            return True
        vim_command('edit %s %s' % (options, escape_file_path(path)))
    # sometimes syntax is being disabled and the filetype not set.
    if int(vim_eval('!exists("g:syntax_on")')) == 1:
        vim_command('syntax enable')
    if int(vim_eval("&filetype != 'python'")) == 1:
        vim_command('set filetype=python')
    return True


@catch_and_print_exceptions
def _tabnew(path, options=''):
    """
    Open a file in a new tab or switch to an existing one.

    :param options: `:tabnew` options, read vim help.
    """
    if int(vim_eval('has("gui")')) == 1:
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
                if os.path.abspath(buf_path) == os.path.abspath(path):
                    # tab exists, just switch to that tab
                    vim_command('tabfirst | tabnext %i' % (tab_nr + 1))
                    # Goto the buffer's window.
                    vim_command('exec bufwinnr(%i) . " wincmd w"' % (buf_nr + 1))
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
