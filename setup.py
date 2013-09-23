from setuptools import setup
from setuptools import find_packages

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='downflickr',
    description='Download photoset of flickr using gevent',
    long_description=open('README.rst').read(),
    version='0.0.1',
    author='carlcarl',
    author_email='carlcarlking@gmail.com',
    url='https://github.com/carlcarl/downflickr',
    packages=find_packages(),
    install_requires=required,
    license='MIT',
    entry_points={
        'console_scripts': [
            'downflickr = downflickr.downflickr:main',
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
