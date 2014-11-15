import os
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
        pytest.main("test.py")

# get requirements
requirements = [r.strip() for r in open('requirements.txt')]

setup(
    name = 'unbound',
    version = '0.0.1',
    author = 'Ed Summers',
    author_email = 'ehs@pobox.com',
    py_modules = ['unbind'],
    scripts = ['bin/unbind'],
    description = 'Write SGA TEI as SharedCanvas',
    cmdclass = {'test': PyTest},
    install_requires = requirements,
    tests_require=['pytest'],
)