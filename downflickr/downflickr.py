#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    import gevent
except ImportError:
    pass
else:
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
logger.setLevel(logging.DEBUG)


class Flickr(object):

    def __init__(self):
        self.url = 'http://flickr.com/services/rest/'
        self.directory = ''
        self.image_size_mode = 1
        self.counter = 0

    def read_config(self):
        parser = SafeConfigParser()
        parser.read('downflickr.conf')
        self.api_key = parser.get('flickr', 'API_KEY')
        self.api_secret = parser.get('flickr', 'API_SECRET')

    def _get_request_args(self, method, **kwargs):
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
            ('api_key', self.api_key),
            ('format', 'json'),
            ('method', method),
            ('nojsoncallback', '1'),
        ]
        if kwargs:
            for key, value in kwargs.iteritems():
                args.append((key, value))
        args.sort(key=lambda tup: tup[0])
        api_sig = self._get_api_sig(args)
        args.append(api_sig)
        return args

    def _get_api_sig(self, args):
        '''
        Flickr API need a hash string which made using post arguments
        Args:
            args: Post args(list)
        Returns:
            api_sig: A tuple of api_sig, ex: ('api_sig', 'abcdefg')
        '''
        tmp_sig = self.api_secret
        for i in args:
            tmp_sig = tmp_sig + i[0] + i[1]
        api_sig = md5.new(tmp_sig.encode('utf-8')).hexdigest()
        return ('api_sig', api_sig)

    def create_dir(self, path):
        if os.path.exists(path):
            if not os.path.isdir(path):
                logger.error('{path} is not a directory'.format(path=path))
                sys.exit(1)
            else:  # ignore
                pass
        else:
            os.makedirs(path)
            logger.info('Create dir: {dir}'.format(dir=path))

    def get_photos_info(self, photoset_id):
        args = self._get_request_args(
            'flickr.photosets.getPhotos',
            photoset_id=photoset_id
        )
        resp = requests.post(self.url, data=args)
        resp_json = json.loads(resp.text.encode('utf-8'))
        logger.debug(resp_json)
        photos = resp_json['photoset']['photo']
        return photos

    def get_photo_url(self, photo_id):
        args = self._get_request_args(
            'flickr.photos.getSizes',
            photo_id=photo_id
        )
        resp = requests.post(self.url, data=args)
        resp_json = json.loads(resp.text.encode('utf-8'))
        logger.debug(json.dumps(resp_json, indent=2))
        size_list = resp_json['sizes']['size']
        size_list_len = len(size_list)
        image_size_mode = size_list_len if size_list_len < self.image_size_mode \
            else self.image_size_mode
        download_url = resp_json['sizes']['size'][-image_size_mode]['source']
        return download_url

    def download_photo(self, photo):
        counter_lock = multiprocessing.Lock()
        photo_id = photo['id']
        photo_title = photo['title']
        download_url = self.get_photo_url(photo_id)
        photo_format = download_url.split('.')[-1]
        photo_title = photo_title + '.' + photo_format
        file_path = self.directory + os.sep + photo_title
        logger.info('Download {photo_title}...'.format(photo_title=photo_title))
        resp = requests.get(download_url)
        with open(file_path, 'w') as f:
            f.write(resp.content)
            with counter_lock:
                self.counter.value -= 1
            logger.info(
                'The number of pictures remaining: {num}'.format(num=self.counter.value)
            )

    def single_download_photos(self, photos):
        self.counter = multiprocessing.Value('i', len(photos))
        for photo in photos:
            self.download_photo(photo)

    def multiple_download_photos(self, photos):
        def init(args):
            self.counter = args
        file_num = multiprocessing.Value('i', len(photos))
        pool = multiprocessing.Pool(
            initializer=init,
            initargs=(file_num, )
        )
        pool.map(self.download_photo, photos)
        pool.close()
        pool.join()

    def event_download_photos(self, photos):
        try:
            assert gevent
        except NameError:
            logger.error('You need install gevent module. Aborting...')
            sys.exit(1)
        self.counter = multiprocessing.Value('i', len(photos))
        jobs = [gevent.spawn(self.download_photo, photo) for photo in photos]
        gevent.joinall(jobs)


def _init_logger():
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    console = logging.StreamHandler(stream=sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    logger.addHandler(console)


def main():
    _init_logger()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-g',
        help='The photoset id to be downloaded',
        metavar='<photoset_id>'
    )
    parser.add_argument(
        '-s',
        default=1,
        help=(
            'Image size. 12 is smallest, 1 is original size. '
            'Default: 1'
        ),
        type=int,
        choices=xrange(0, 10),
        metavar='<num>'
    )
    parser.add_argument(
        '-d',
        help=(
            'The path to store the downloaded images. '
            'Automatically create it if not exist. '
            'Default use the photoset id as folder name under current path'
        ),
        metavar='<path>'
    )
    parser.add_argument(
        '-O',
        default=2,
        help=(
            '0 for single process, '
            '1 for multiprocess, '
            '2 for event driven. '
            'Default: 2'
        ),
        type=int,
        choices=xrange(0, 3),
        metavar='<num>'
    )
    args = parser.parse_args()
    logger.debug(args)

    flickr = Flickr()
    flickr.read_config()

    photoset_id = args.g
    photos = flickr.get_photos_info(photoset_id)
    flickr.image_size_mode = args.s
    d = args.d if args.d else photoset_id
    flickr.directory = d
    flickr.create_dir(d)

    if args.O == 0:
        flickr.single_download_photos(photos)
    elif args.O == 1:
        flickr.multiple_download_photos(photos)
    elif args.O == 2:
        try:
            assert gevent
        except NameError:
            logger.warn('gevent not exist, fallback to multiprocess...')
            flickr.multiple_download_photos(photos)
        else:
            flickr.event_download_photos(photos)
    else:
        logger.error('Unknown Error')


if __name__ == '__main__':
    main()
