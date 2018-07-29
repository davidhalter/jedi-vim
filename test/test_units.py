import subprocess
import time
import shlex

import pytest


class VimError(Exception):
    pass


class Vim:
    def __init__(self, exe, servername):
        self.base_args = [exe, '-u', 'NONE', '--not-a-term',
                          '--servername', servername]
        cmd = self.base_args + ['--startuptime', '/tmp/s']
        print('Running: %s' % ' '.join(shlex.quote(x) for x in cmd))
        self._server = self._popen_vim(cmd)
        self._wait_for_server()

    def _popen_vim(self, cmd):
        return subprocess.Popen(cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                stdin=subprocess.DEVNULL)

    def _wait_for_server(self):
        waited = 0
        while not self._eval('1', ignore_error=True):
            time.sleep(0.1)
            waited += 0.1
        print('waited: %.2f' % waited)

    def _eval(self, expr, ignore_error=False):
        proc = self._popen_vim(self.base_args + ['--remote-expr', expr])
        (stdout, stderr) = proc.communicate()
        if not ignore_error:
            if stderr:
                raise VimError('Error with --remote-expr: %s' % (stderr,))
            assert proc.returncode == 0
        return stdout.decode('utf-8').rstrip('\n')

    def eval(self, expr):
        return self._eval(expr)

    def sendkeys(self, keys):
        proc = self._popen_vim(self.base_args + ['--remote-send', keys])
        (stdout, stderr) = proc.communicate()
        if stderr:
            raise VimError('Error with --remote-expr: %s' % (stderr,))
        assert proc.returncode == 0


@pytest.fixture(scope='session')
def vim_exe():
    return 'vim'


@pytest.fixture(scope='session')
def vim_servername():
    return 'JEDI-VIM-TESTS'


@pytest.fixture(scope='session')
def vim(vim_exe, vim_servername):
    return Vim(vim_exe, vim_servername)


def test_smoke(vim):
    """Tests that this mechanism works."""
    assert vim.eval('1')
    vim.sendkeys('ifoo')
    assert vim.eval('getline(".")') == 'foo'
    vim.sendkeys('dd')
    assert vim.eval('getline(".")') == 'foodd'
    vim.sendkeys(r'\<Esc>dd')
    assert vim.eval('getline(".")') == ''
