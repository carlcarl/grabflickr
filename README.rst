grabflickr
==========
Download photoset of flickr, support single process, multithread and gevent(Asynchronous I/O)

Installation
------------
::

	sudo python setup.py install

or::

    sudo pip install grabflickr


gevent
~~~~~~

Notice: Without libevent, grabflickr will fallback to normal multithread download

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

Method Benchmark(sec)
----------------------------

:: 

    /usr/bin/time -p ./grabflickr.py -g xxxxxxxxx -O num -s 6

single multiprocess
~~~~~~~~~~~~~~~~~~~
* 31.37

multiprocess
~~~~~~~~~~~~
* 9.91
* 8.24
* 7.49

gevent
~~~~~~
* 7.87
* 7.94
* 7.66

