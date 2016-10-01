# The MIT License (MIT)
#
# Copyright (c) 2015 DonJayamanne
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import io
import re
import sys
import json
import traceback
sys.path.append(os.path.dirname(__file__))
import jedi
# remove jedi from path after we import it so it will not be completed
sys.path.pop(0)

WORD_RE = re.compile(r'\w')


class JediCompletion(object):
    basic_types = {
        'module': 'import',
        'instance': 'variable',
        'statement': 'value',
        'param': 'variable',
    }

    def __init__(self):
        self.default_sys_path = sys.path
        self._input = io.open(sys.stdin.fileno(), encoding='utf-8')

    def _get_definition_type(self, definition):
        is_built_in = definition.in_builtin_module
        if definition.type not in ['import', 'keyword'] and is_built_in():
            return 'builtin'
        if definition.type in ['statement'] and definition.name.isupper():
            return 'constant'
        return self.basic_types.get(definition.type, definition.type)

    def _additional_info(self, completion):
        """Provide additional information about the completion object."""
        if completion._definition is None:
            return ''
        if completion.type == 'statement':
            nodes_to_display = ['InstanceElement', 'String', 'Node', 'Lambda',
                                'Number']
            return ''.join(c.get_code() for c in
                           completion._definition.children if type(c).__name__
                           in nodes_to_display).replace('\n', '')
        return ''

    @classmethod
    def _get_top_level_module(cls, path):
        """Recursively walk through directories looking for top level module.

        Jedi will use current filepath to look for another modules at same
        path, but it will not be able to see modules **above**, so our goal
        is to find the higher python module available from filepath.
        """
        _path, _ = os.path.split(path)
        if os.path.isfile(os.path.join(_path, '__init__.py')):
            return cls._get_top_level_module(_path)
        return path

    def _generate_signature(self, completion):
        """Generate signature with function arguments.
        """
        if not hasattr(completion, 'params'):
            return ''
        return '%s(%s)' % (
            completion.name,
            ', '.join(param.description for param in completion.params))

    def _get_call_signatures(self, script):
        """Extract call signatures from jedi.api.Script object in failsafe way.

        Returns:
            Tuple with original signature object, name and value.
        """
        _signatures = []
        try:
            call_signatures = script.call_signatures()
        except KeyError:
            call_signatures = []
        for signature in call_signatures:
            for pos, param in enumerate(signature.params):
                if not param.name:
                    continue
                if param.name == 'self' and pos == 0:
                    continue
                if WORD_RE.match(param.name) is None:
                    continue
                try:
                    name, value = param.description.split('=')
                except ValueError:
                    name = param.description
                    value = None
                if name.startswith('*'):
                    continue
                _signatures.append((signature, name, value))
        return _signatures

    def _get_call_signatures_with_args(self, script):
        """Extract call signatures from jedi.api.Script object in failsafe way.

        Returns:
            Array with dictionary
        """
        _signatures = []
        try:
            call_signatures = script.call_signatures()
        except KeyError:
            call_signatures = []
        for signature in call_signatures:
            sig = {"name": "", "description": "", "docstring": "",
                   "paramindex": 0, "params": [], "bracketstart": []}
            sig["description"] = signature.description
            sig["docstring"] = signature.docstring()
            sig["name"] = signature.name
            sig["paramindex"] = signature.index
            sig["bracketstart"].append(signature.index)

            _signatures.append(sig)
            for pos, param in enumerate(signature.params):
                if not param.name:
                    continue
                if param.name == 'self' and pos == 0:
                    continue
                if WORD_RE.match(param.name) is None:
                    continue
                try:
                    name, value = param.description.split('=')
                except ValueError:
                    name = param.description
                    value = None
                #if name.startswith('*'):
                #    continue
                #_signatures.append((signature, name, value))
                sig["params"].append({"name": name, "value":value, "docstring":param.docstring(), "description":param.description})
        return _signatures

    def _serialize_completions(self, script, identifier=None, prefix=''):
        """Serialize response to be read from VSCode.

        Args:
            script: Instance of jedi.api.Script object.
            identifier: Unique completion identifier to pass back to VSCode.
            prefix: String with prefix to filter function arguments.
                Used only when fuzzy matcher turned off.

        Returns:
            Serialized string to send to VSCode.
        """
        _completions = []

        for signature, name, value in []: # self._get_call_signatures(script):
            if not self.fuzzy_matcher and not name.lower().startswith(
              prefix.lower()):
                continue
            _completion = {
                'type': 'property',
                'rightLabel': self._additional_info(signature)
            }
            # we pass 'text' here only for fuzzy matcher
            if value:
                _completion['snippet'] = '%s=${1:%s}$0' % (name, value)
                _completion['text'] = '%s=%s' % (name, value)
            else:
                _completion['snippet'] = '%s=$1$0' % name
                _completion['text'] = name
                _completion['displayText'] = name
            if self.show_doc_strings:
                _completion['description'] = signature.docstring()
            else:
                _completion['description'] = self._generate_signature(
                    signature)
            _completions.append(_completion)

        try:
            completions = script.completions()
        except KeyError:
            completions = []
        for completion in completions:
            if self.show_doc_strings:
                description = completion.docstring()
            else:
                description = self._generate_signature(completion)
            _completion = {
                'text': completion.name,
                'type': self._get_definition_type(completion),
                'description': description,
                'rightLabel': self._additional_info(completion)
            }
            # for jedi-vim
            _completion = {
                'name': completion.name,
                'complete': completion.complete,
                'name_with_symbols': completion.name_with_symbols,
                'description': completion.description,
                'docstring_': completion.docstring(),
            }
            # if any([c['text'].split('=')[0] == _completion['text']
            #         for c in _completions]):
            #   # ignore function arguments we already have
            #   continue
            _completions.append(_completion)
        return json.dumps({'id': identifier, 'results': _completions})

    def _serialize_arguments(self, script, identifier=None):
        """Serialize response to be read from VSCode.

        Args:
            script: Instance of jedi.api.Script object.
            identifier: Unique completion identifier to pass back to VSCode.

        Returns:
            Serialized string to send to VSCode.
        """
        return json.dumps({"id": identifier, "results" : self._get_call_signatures_with_args(script) })

    def _get_call_signatures_jp(self, script):
        """Extract call signatures from jedi.api.Script object in failsafe way.

        Returns:
            Dict representation of parts of signature needed by jedi-vim
        """
        _signatures = []
        try:
            call_signatures = script.call_signatures()
        except KeyError:
            call_signatures = []

        for signature in call_signatures:
            params = [{'description': p.description} for p in signature.params]
            _signatures.append({
                'params': params,
                'bracket_start': signature.bracket_start,
                'index': signature.index
            })

        return _signatures

    def _serialize_signatures(self, script, identifier=None):
        """Serialize call signatures to be read by jedi_client"""
        return json.dumps({'id': identifier, 'results': self._get_call_signatures_jp(script)})

    def _serialize_definitions(self, definitions, identifier=None):
        """Serialize response to be read from VSCode.

        Args:
            definitions: List of jedi.api.classes.Definition objects.
            identifier: Unique completion identifier to pass back to VSCode.

        Returns:
            Serialized string to send to VSCode.
        """

        def _top_definition(definition):
          for d in definition.goto_assignments():
            if d == definition:
              continue
            if d.type == 'import':
              return _top_definition(d)
            else:
              return d
          return definition

        _definitions = []
        for definition in definitions:
            try:
                if definition.module_path:
                    if definition.type == 'import':
                        definition = _top_definition(definition)

                    _definition = {
                        'text': definition.name,
                        'type': self._get_definition_type(definition),
                        'fileName': definition.module_path,
                        'line': definition.line - 1,
                        'column': definition.column
                    }
                    _definitions.append(_definition)
            except Exception as e:
                pass
        return json.dumps({'id': identifier, 'results': _definitions})

    def _serialize_usages(self, usages, identifier=None):
      _usages = []
      for usage in usages:
        _usages.append({
          'name': usage.name,
          'moduleName': usage.module_name,
          'fileName': usage.module_path,
          'line': usage.line,
          'column': usage.column,
        })
      return json.dumps({'id': identifier, 'results': _usages})

    def _deserialize(self, request):
        """Deserialize request from VSCode.

        Args:
            request: String with raw request from VSCode.

        Returns:
            Python dictionary with request data.
        """
        return json.loads(request)

    def _set_request_config(self, config):
        """Sets config values for current request.

        This includes sys.path modifications which is getting restored to
        default value on each request so each project should be isolated
        from each other.

        Args:
            config: Dictionary with config values.
        """
        sys.path = self.default_sys_path
        self.use_snippets = config.get('useSnippets')
        self.show_doc_strings = config.get('showDescriptions', True)
        self.fuzzy_matcher = config.get('fuzzyMatcher', False)
        jedi.settings.case_insensitive_completion = config.get(
            'caseInsensitiveCompletion', True)
        for path in config.get('extraPaths', []):
            if path and path not in sys.path:
                sys.path.insert(0, path)

    def _process_request(self, request):
        """Accept serialized request from VSCode and write response.
        """
        request = self._deserialize(request)

        self._set_request_config(request.get('config', {}))

        path = self._get_top_level_module(request.get('path', ''))
        if path not in sys.path:
            sys.path.insert(0, path)
        lookup = request.get('lookup', 'completions')

        if lookup == 'names':
            return self._write_response(self._serialize_definitions(
                jedi.api.names(
                    source=request.get('source', None),
                    path=request.get('path', ''),
                    all_scopes=True),
                request['id']))

        script = jedi.api.Script(
            source=request.get('source', None), line=request['line'] + 1,
            column=request['column'], path=request.get('path', ''))

        if lookup == 'definitions':
            return self._write_response(self._serialize_definitions(
                script.goto_assignments(), request['id']))
        elif lookup == 'arguments':
            return self._write_response(self._serialize_arguments(
                script, request['id']))
        elif lookup == 'usages':
            return self._write_response(self._serialize_usages(
                script.usages(), request['id']))
        elif lookup == 'signatures':
            return self._write_response(self._serialize_signatures(
                script, request['id']))
        else:
            return self._write_response(
                self._serialize_completions(script, request['id'],
                                            request.get('prefix', '')))

    def _write_response(self, response):
        sys.stdout.write(response + '\n')
        sys.stdout.flush()
        return response

    def watch(self):
        while True:
            try:
                self._process_request(self._input.readline())
            except Exception:
                sys.stdout.write('\n')
                sys.stdout.flush()
                sys.stderr.write(traceback.format_exc() + '\n')
                sys.stderr.flush()

if __name__ == '__main__':
    JediCompletion().watch()
