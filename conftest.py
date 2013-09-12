import os
import urllib
import zipfile
import subprocess

CACHE_FOLDER = '.cache'
VSPEC_FOLDER = os.path.join(CACHE_FOLDER, 'vim-vspec-master')
VSPEC_RUNNER = os.path.join(VSPEC_FOLDER, 'bin/vspec')
TEST_DIR = 'test'


class IntegrationTestFile(object):
    def __init__(self, path):
        self.path = path

    def run(self):
        output = subprocess.check_output([VSPEC_RUNNER, '.', VSPEC_FOLDER, self.path])
        for line in output.splitlines():
            if line.startswith('not ok') or line.startswith('Error'):
                print(output)
                assert False

    def __repr__(self):
        return "<%s: %s>"  % (type(self), self.path)


def pytest_configure(config):
    if not os.path.isdir(CACHE_FOLDER):
        os.mkdir(CACHE_FOLDER)

    if not os.path.exists(VSPEC_FOLDER):
        url = 'https://github.com/kana/vim-vspec/archive/master.zip'
        name, hdrs = urllib.urlretrieve(url)
        z = zipfile.ZipFile(name)
        for n in z.namelist():
            dest = os.path.join(CACHE_FOLDER, n)
            destdir = os.path.dirname(dest)
            if not os.path.isdir(destdir):
              os.makedirs(destdir)
            data = z.read(n)
            if not os.path.isdir(dest):
                with open(dest, 'w') as f:
                    f.write(data)
        z.close()
        os.chmod(VSPEC_RUNNER, 0777)


def pytest_generate_tests(metafunc):
    """
    :type metafunc: _pytest.python.Metafunc
    """
    def collect_tests():
        for f in os.listdir(TEST_DIR):
            if f.endswith('.vim'):
                yield IntegrationTestFile(os.path.join(TEST_DIR, f))

    metafunc.parametrize('case', list(collect_tests()))
