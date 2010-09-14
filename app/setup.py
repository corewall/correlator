
from distutils.core import setup, Extension
import os

coreDir = os.environ["CORE_DIRECTORY"]

module1 = Extension('py_correlator',
                    include_dirs = [coreDir + '/include'],
                    libraries = ['core'],
                    library_dirs = [coreDir + '/lib'],
                    sources = ['py_func.cpp'])

setup (name = 'py_correlator',
       version = '0.1',
       author = 'Hyejung Hur',
       description = 'This is a python-correlator interface that enables you to use python for correlator apps',
       ext_modules = [module1])
