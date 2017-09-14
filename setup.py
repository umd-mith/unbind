import os
import sys

from setuptools import setup, Command

class PyTest(Command):
    """
    A command to convince setuptools to run pytests.
    """
    user_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    def run(self):
        import pytest
        errno = pytest.main("test.py")
        sys.exit(errno)

setup(
    name = 'unbind',
    version = '0.0.1',
    author = 'Ed Summers',
    author_email = 'ehs@pobox.com',
    packages = ['unbind'],
    scripts = ['bin/unbind'],
    description = 'Write SGA TEI as SharedCanvas',
    cmdclass = {'test': PyTest},
    tests_require=['pytest'],
)
