#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gevent
from gevent import monkey
monkey.patch_all()
import sys
import os
import md5
import json
import logging
import argparse
import multiprocessing
from ConfigParser import SafeConfigParser
import requests


logger = logging.getLogger(__name__)
api_key = ''
api_secret = ''
url = 'http://flickr.com/services/rest/'
directory = ''
counter = 0


def _get_request_args(method, **kwargs):
    '''
    Use `method` and other settings to produce a flickr API arguments.
    Here also use json as the return type.
    Args:
        method: The method string provided by flickr,
            ex: flickr.photosets.getPhotos
        **kwargs: Other settings
    Returns:
        args: An argument list used for post request
    '''
    args = [
        ('api_key', api_key),
        ('format', 'json'),
        ('method', method),
        ('nojsoncallback', '1'),
    ]
    if kwargs:
        for key, value in kwargs.iteritems():
            args.append((key, value))
    args.sort(key=lambda tup: tup[0])
    api_sig = _get_api_sig(args)
    args.append(api_sig)
    return args


def _get_api_sig(args):
    '''
    Flickr API need a hash string which made using post arguments
    Args:
        args: Post args(list)
    Returns:
        api_sig: A tuple of api_sig, ex: ('api_sig', 'abcdefg')
    '''
    tmp_sig = api_secret
    for i in args:
        tmp_sig = tmp_sig + i[0] + i[1]
    api_sig = md5.new(tmp_sig.encode('utf-8')).hexdigest()
    return ('api_sig', api_sig)


def init_logger():
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    console = logging.StreamHandler(stream=sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    logger.addHandler(console)
    logger.setLevel(logging.INFO)


def get_photos_info(photoset_id):
    args = _get_request_args(
        'flickr.photosets.getPhotos',
        photoset_id=photoset_id
    )
    resp = requests.post(url, data=args)
    resp_json = json.loads(resp.text.encode('utf-8'))
    logger.debug(resp_json)
    photos = resp_json['photoset']['photo']
    return photos


def create_dir(path):
    if os.path.exists(path):
        if not os.path.isdir(path):
            logger.error('{path} is not a directory'.format(path=path))
            sys.exit(1)
        else:  # ignore
            pass
    else:
        os.makedirs(path)
        logger.info('Create dir: {dir}'.format(dir=path))


def get_photo_url(photo_id):
    args = _get_request_args(
        'flickr.photos.getSizes',
        photo_id=photo_id
    )
    resp = requests.post(url, data=args)
    resp_json = json.loads(resp.text.encode('utf-8'))
    logger.debug(resp_json)
    download_url = resp_json['sizes']['size'][-1]['source']
    return download_url


def download_photo(photo):
    counter_lock = multiprocessing.Lock()
    photo_id = photo['id']
    photo_title = photo['title']
    download_url = get_photo_url(photo_id)
    photo_format = download_url.split('.')[-1]
    photo_title = photo_title + '.' + photo_format
    file_path = directory + os.sep + photo_title
    logger.info('Download {photo_title}...'.format(photo_title=photo_title))
    resp = requests.get(download_url)
    with open(file_path, 'w') as f:
        f.write(resp.content)
        global counter
        with counter_lock:
            counter.value -= 1
        logger.info(
            'The number of pictures remaining: {num}'.format(num=counter.value)
        )


def single_download_photos(photos):
    global counter
    counter = multiprocessing.Value('i', len(photos))
    for photo in photos:
        download_photo(photo)


def multiple_download_photos(photos):
    def init(args):
        global counter
        counter = args
    file_num = multiprocessing.Value('i', len(photos))
    pool = multiprocessing.Pool(
        initializer=init,
        initargs=(file_num, )
    )
    pool.map(download_photo, photos)
    pool.close()
    pool.join()


def event_download_photos(photos):
    global counter
    counter = multiprocessing.Value('i', len(photos))
    jobs = [gevent.spawn(download_photo, photo) for photo in photos]
    gevent.joinall(jobs)


def read_config():
    parser = SafeConfigParser()
    parser.read('downflickr.conf')
    global api_key, api_secret
    api_key = parser.get('flickr', 'API_KEY')
    api_secret = parser.get('flickr', 'API_SECRET')


def main():
    init_logger()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-s',
        help='Photoset id'
    )
    args = parser.parse_args()

    read_config()
    photoset_id = args.s
    global directory
    directory = photoset_id
    photos = get_photos_info(photoset_id)
    create_dir(photoset_id)
    # single_download_photos(photos)
    # multiple_download_photos(photos)
    event_download_photos(photos)


if __name__ == '__main__':
    main()
