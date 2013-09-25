grabflickr
==========
Download photoset of flickr, support single process, multiprocess and gevent(Asynchronous I/O)

Installation
------------
::

	sudo python setup.py install

or::

    sudo pip install grabflickr


gevent
~~~~~~

Notice: Without libevent, grabflickr will fallback to normal multiprocess download

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
    gf -u

    # Download photoset
    gf -g <photoset id>

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
