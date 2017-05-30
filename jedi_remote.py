import json
import os
import sys

# add path for jedi
sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jedi'))

import jedi


class PoorRPC(object):
    def __init__(self, input=None, output=None):
        if input is None:
            input = sys.stdin

        if output is None:
            output = sys.stdout

        self.input = input
        self.output = output

        self.script = None

    def run(self):
        for line in iter(self.input.readline, ''):
            data = json.loads(line)

            try:
                func = getattr(self, 'func_' + data['func'])
                ret = func(*data['args'], **data['kwargs'])
            except Exception as e:
                result = {'code': 'ng', 'message': repr(e)}
            else:
                result = {'code': 'ok', 'return': ret}

            self._write_output(result)

    def _write_output(self, data):
        self.output.write(json.dumps(data))
        self.output.write('\n')
        self.output.flush()

    def func_set_additional_dynamic_modules(self, modules):
        jedi.settings.additional_dynamic_modules = modules

    def func_set_script(self, *args, **kwargs):
        self.script = jedi.Script(*args, **kwargs)

    def func_completions(self):
        return [_completion2dict(c) for c in self.script.completions()]

    def func_call_signatures(self):
        return [_signiture2dict(s) for s in self.script.call_signatures()]

    def func_goto_definitions(self):
        return [_definition2dict(d) for d in self.script.goto_definitions()]

    def func_goto_assignments(self):
        return [_definition2dict(d) for d in self.script.goto_assignments()]

    def func_usages(self):
        return [_definition2dict(d) for d in self.script.usages()]


def _completion2dict(comp):
    d = _obj2dict(comp, 'name', 'complete', 'description')
    d['docstring'] = comp.docstring()

    return d


def _signiture2dict(sig):
    return _obj2dict(sig, 'bracket_start', 'params', 'index')


def _definition2dict(defi):
    d = _obj2dict(defi,
                  'is_keyword', 'desc_with_module', 'module_path',
                  'description', 'name', 'line', 'column')
    d['in_builtin_module'] = defi.in_builtin_module()
    d['docstring'] = defi.docstring()

    return d


def _obj2dict(obj, *names):
    return {n: getattr(obj, n) for n in names}


if __name__ == '__main__':
    rpc = PoorRPC()
    rpc.run()
