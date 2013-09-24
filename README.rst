downflickr
==========
Download photoset of flickr using gevent(Asynchronous I/O)

Installation
------------
::

	sudo python setup.py install


gevent
~~~~~~

In Mac
++++++
::

    brew install libevent

In Linux
++++++++
::

    apt-get install libevent-dev
    apt-get install python-all-dev 

Usage
-----
::

    # Enter your api key
    downflickr -u

    # Download photoset
    downflickr -g xxx

Method Benchmark(min:sec)
----------------------------
single multiprocess
~~~~~~~~~~~~~~~~~~~
* 3:27.72
* 3:30.16
* 4:07.44
* 3:35.17

multiprocess
~~~~~~~~~~~~
* 1:48.51
* 1:42.09
* 1:33.29
* 1:58.08

gevent
~~~~~~
* 1:13.83
* 1:10.13
