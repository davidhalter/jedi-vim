import os
import subprocess
import urllib.request
import zipfile

import pytest

VSPEC_URL = 'https://github.com/kana/vim-vspec/archive/1.4.1.zip'
CACHE_FOLDER = 'build'
VSPEC_FOLDER = os.path.join(CACHE_FOLDER, 'vim-vspec-1.4.1')
VSPEC_RUNNER = os.path.join(VSPEC_FOLDER, 'bin/vspec')
TEST_DIR = 'test'


class IntegrationTestFile(object):
    def __init__(self, path):
        self.path = path

    def run(self):
        output = subprocess.check_output(
            [VSPEC_RUNNER, '.', VSPEC_FOLDER, self.path])
        had_ok = False
        for line in output.splitlines():
            if (line.startswith(b'not ok') or
                    line.startswith(b'Error') or
                    line.startswith(b'Bail out!')):
                pytest.fail("{0} failed:\n{1}".format(
                    self.path, output.decode('utf-8')), pytrace=False)
            if not had_ok and line.startswith(b'ok'):
                had_ok = True
        if not had_ok:
            pytest.fail("{0} failed: no 'ok' found:\n{1}".format(
                self.path, output.decode('utf-8')), pytrace=False)

    @property
    def name(self):
        name = os.path.basename(self.path)
        name, _, _ = name.rpartition('.')
        return name

    def __repr__(self):
        return "<%s: %s>" % (type(self), self.path)


def pytest_configure(config):
    if not os.path.isdir(CACHE_FOLDER):
        os.mkdir(CACHE_FOLDER)

    if not os.path.exists(VSPEC_FOLDER):
        name, hdrs = urllib.request.urlretrieve(VSPEC_URL)
        z = zipfile.ZipFile(name)
        for n in z.namelist():
            dest = os.path.join(CACHE_FOLDER, n)
            destdir = os.path.dirname(dest)
            if not os.path.isdir(destdir):
                os.makedirs(destdir)
            data = z.read(n)
            if not os.path.isdir(dest):
                with open(dest, 'wb') as f:
                    f.write(data)
        z.close()
        os.chmod(VSPEC_RUNNER, 0o777)


def pytest_generate_tests(metafunc):
    """
    :type metafunc: _pytest.python.Metafunc
    """
    def collect_tests():
        for f in os.listdir(TEST_DIR):
            if f.endswith('.vim') and f != '_utils.vim':
                yield IntegrationTestFile(os.path.join(TEST_DIR, f))

    tests = list(collect_tests())
    metafunc.parametrize('case', tests, ids=[test.name for test in tests])
