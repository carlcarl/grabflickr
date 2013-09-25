from setuptools import setup
from setuptools import find_packages

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='grabflickr',
    description='Download photoset of flickr, support single process, multiprocess and gevent(Asynchronous I/O)',
    long_description=open('README.rst').read(),
    version='0.0.1',
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
        'Development Status :: 3 - Alpha',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Topic :: Utilities',
        'Topic :: Software Development :: Libraries',
    ]
)
