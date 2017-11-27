import os
import re
import sys
from setuptools import setup, find_packages


PY_VER = sys.version_info

if not PY_VER >= (3, 5):
    raise RuntimeError('aiozipkin does not support Python earlier than 3.5')


def read(f):
    return open(os.path.join(os.path.dirname(__file__), f)).read().strip()


install_requires = ['aiohttp']
extras_require = {}


def read_version():
    regexp = re.compile(r"^__version__\W*=\W*'([\d.abrc]+)'")
    init_py = os.path.join(os.path.dirname(__file__),
                           'aiozipkin', '__init__.py')
    with open(init_py) as f:
        for line in f:
            match = regexp.match(line)
            if match is not None:
                return match.group(1)
        else:
            msg = 'Cannot find version in aiozipkin/__init__.py'
            raise RuntimeError(msg)


classifiers = [
    'License :: OSI Approved :: MIT License',
    'Intended Audience :: Developers',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Operating System :: POSIX',
    'Development Status :: 3 - Alpha',
    'Framework :: AsyncIO',
]


setup(name='aiozipkin',
      version=read_version(),
      description=('Distributed tracing instrumentation '
                   'for asyncio application with zipkin'),
      long_description='\n\n'.join((read('README.rst'), read('CHANGES.txt'))),
      classifiers=classifiers,
      platforms=['POSIX'],
      author='Nikolay Novik',
      author_email='nickolainovik@gmail.com',
      url='https://github.com/aio-libs/aiozipkin',
      download_url='https://pypi.python.org/pypi/aiozipkin',
      license='Apache 2',
      packages=find_packages(),
      install_requires=install_requires,
      extras_require=extras_require,
      include_package_data=True)
