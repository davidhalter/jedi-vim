"""
Remote jedi for jedi-vim

Daniel Holth <dholth@gmail.com>, 2016
"""

__version__ = '0.9.0'

import os.path
import attr
import subprocess
import json

import logging
log = logging.getLogger(__name__)

DEBUG = False

if DEBUG:
    log.setLevel(logging.DEBUG)
    fh = logging.FileHandler('/tmp/jedi.log')
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(message)s')
    fh.setFormatter(formatter)
    log.addHandler(fh)

__here__ = os.path.dirname(__file__)

class LineSubprocess(object):
    def __init__(self):
        import distutils.spawn
        self.PYTHON = distutils.spawn.find_executable('python')
        self._child = None

    @property
    def child(self):
        if self._child == None or self._child.poll() != None:
            self._child = subprocess.Popen([self.PYTHON, __here__], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        return self._child

    def request(self, command):
        """Send line to subprocess, returning one-line response."""
        child = self.child
        child.stdin.write(command.encode('utf-8') + b'\n')
        child.stdin.flush()
        return child.stdout.readline().decode('utf-8') # XXX timeout, subprocess MUST send \n and flush()
        # XXX does subprocess need to do something to ensure utf-8 encoding?

server = LineSubprocess()

class Settings(object):
    additional_dynamic_modules = attr.ib(default=[])

settings = Settings()

class NotFoundError(Exception):
    # no longer used, but referenced
    pass

@attr.s
class Completion(object):
    name = attr.ib()
    complete = attr.ib()
    name_with_symbols = attr.ib()
    description = attr.ib()
    docstring_ = attr.ib()

    def docstring(self):
        return self.docstring_

@attr.s
class Param(object):
    description = attr.ib()

@attr.s(init=False)
class CallSignature(object):
    bracket_start = attr.ib()
    index = attr.ib()
    params = attr.ib(default=attr.Factory(list))

    def __getattr__(self, key):
        if not key in self.__dict__:
            log.debug('getattr', key)
        return self.__dict__[key]

    def __init__(self, params=None, bracket_start=None, index=None):
        self.params = [Param(p['description']) for p in params]
        self.bracket_start = bracket_start
        self.index = index

@attr.s
class Script(object):
    sequence = 0

    source = attr.ib(default=None)
    line = attr.ib(default=None)
    column = attr.ib(default=None)
    path = attr.ib(default='')
    encoding = attr.ib(default='utf-8')
    source_path = attr.ib(default=None)
    source_encoding = attr.ib(default=None)
    id = attr.ib(default=0)

    # manual __init__ won't work with attr.ib...

    def request(self, lookup='completions'):
        Script.sequence += 1
        self.id = Script.sequence
        try:
            request_data = self.__dict__.copy()
            request_data['line'] -= 1
            request_data['lookup'] = lookup
            request = json.dumps(request_data, sort_keys=True) # must be 1 line only
            log.debug(request)
            response = server.request(request)
            log.debug("-> %s", response)
            return json.loads(response)['results']
        except Exception as e:
            log.exception(e)

    def completions(self):
        results = self.request(lookup='completions')
        completions = [Completion(**result) for result in results]
        return completions

    def call_signatures(self):
        results = self.request(lookup='signatures')
        signatures = [CallSignature(**result) for result in results]
        return signatures

    def goto_definitions(self):
        result = self.request(lookup='definitions')
        return []

    def goto_assignments(self):
        return []

    def usages(self):
        results = self.request(lookup='usages')
        return []

