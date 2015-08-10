from setuptools import setup
from setuptools import find_packages

import re
import os
def get_release():
    regexp = re.compile(r"^__version__\W*=\W*'([\d.abrc]+)'")
    root = os.path.dirname(__file__)
    init_py = os.path.join(root, 'grabflickr', '__init__.py')
    with open(init_py) as f:
        for line in f:
            match = regexp.match(line)
            if match is not None:
                return match.group(1)
        else:
            raise RuntimeError('Cannot find version in grabflickr/__init__.py')


with open('requirements.txt') as f:
    required = f.read().splitlines()


setup(
    name='grabflickr',
    description='Download photoset of flickr, support single process, multiprocess and gevent(Asynchronous I/O)',
    long_description=open('README.rst').read(),
    version=get_release(),
    author='carlcarl',
    author_email='carlcarlking@gmail.com',
    url='https://github.com/carlcarl/grabflickr',
    packages=find_packages(),
    install_requires=required,
    license='MIT',
    entry_points={
        'console_scripts': [
            'gf = grabflickr.grabflickr:main',
        ]
    },

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2 :: Only',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Topic :: Utilities',
        'Topic :: Software Development :: Libraries',
    ]
)
