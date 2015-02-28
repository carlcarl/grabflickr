#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    import gevent
except ImportError:
    pass
else:
    from gevent import monkey
import sys
import os
import hashlib
import json
import logging
import argparse
import multiprocessing
from ConfigParser import SafeConfigParser
import requests


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
url = 'http://flickr.com/services/rest/'
directory = ''
image_size_mode = 1
counter = 0
CONFIG_PATH = os.path.expanduser('~/.grabflickr.conf')
api_key = ''
api_secret = ''

SINGLE_PROCESS = 0
MULTIPROCESS = 1
GEVENT = 2


def read_config():
    """Read the config from CONFIG_PATH(Default: ~/.grabflickr.conf)
    This will prompt for API key and secret if it not exists.
    After, it sets the global variable `api_key` and `api_secret`.
    """
    parser = SafeConfigParser()
    parser.read(CONFIG_PATH)
    if not parser.has_section('flickr'):
        logger.info('Seems you don\'t set API key, please enter the following informations: ')
        enter_api_key(parser)
    global api_key, api_secret
    api_key = parser.get('flickr', 'API_KEY')
    api_secret = parser.get('flickr', 'API_SECRET')


def enter_api_key(parser=None):
    """Prompt for API key and secret
    Then write them to CONFIG_PATH(Default: ~/.grabflickr.conf)

    :param parser: Config parser
    :type parser: SafeConfigParser
    """
    if parser is None:
        parser = SafeConfigParser()
    parser.add_section('flickr')
    global api_key, api_secret
    api_key = raw_input('Enter your API key: ')
    api_secret = raw_input('Enter your API secret: ')
    parser.set('flickr', 'API_KEY', api_key)
    parser.set('flickr', 'API_SECRET', api_secret)
    with open(CONFIG_PATH, 'wb') as f:
        parser.write(f)


def _get_request_args(method, **kwargs):
    """Use `method` and other settings to produce a flickr API arguments.
    Here also use json as the return type.

    :param method: The method provided by flickr,
            ex: flickr.photosets.getPhotos
    :type method: str
    :param kwargs: Other settings
    :type kwargs: dict
    :return: An argument list used for post request
    :rtype: list of sets
    """
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
    """Flickr API need a hash string which made using post arguments

    :param args: Arguments of the flickr request
    :type args: list of sets
    :return: api_sig, ex: ('api_sig', 'abcdefg')
    :rtype: tuple
    """
    tmp_sig = api_secret
    for i in args:
        tmp_sig = tmp_sig + i[0] + i[1]
    api_sig = hashlib.md5(tmp_sig.encode('utf-8')).hexdigest()
    return 'api_sig', api_sig


def create_dir(path):
    """Create dir with the path

    :param path: The path to be created
    :type path: str
    """
    if os.path.exists(path):
        if not os.path.isdir(path):
            logger.error('%s is not a directory', path)
            sys.exit(1)
        else:  # ignore
            pass
    else:
        os.makedirs(path)
        logger.info('Create dir: %s', path)


def get_photos_info(photoset_id):
    """Request the photos information with the photoset id

    :param photoset_id: The photoset id of flickr
    :type photoset_id: str
    :return: photos information
    :rtype: list
    """
    args = _get_request_args(
        'flickr.photosets.getPhotos',
        photoset_id=photoset_id
    )
    resp = requests.post(url, data=args)
    resp_json = json.loads(resp.text.encode('utf-8'))
    logger.debug(resp_json)
    photos = resp_json['photoset']['photo']
    return photos


def get_photo_url(photo_id):
    """Request the photo download url with the photo id
    :param photo_id: The photo id of flickr
    :type photo_id: str
    :return: Photo download url
    :rtype: str
    """
    args = _get_request_args(
        'flickr.photos.getSizes',
        photo_id=photo_id
    )
    resp = requests.post(url, data=args)
    resp_json = json.loads(resp.text.encode('utf-8'))
    logger.debug(json.dumps(resp_json, indent=2))
    size_list = resp_json['sizes']['size']
    size_list_len = len(size_list)
    global image_size_mode
    image_size_mode = size_list_len if size_list_len < image_size_mode \
        else image_size_mode
    download_url = resp_json['sizes']['size'][-image_size_mode]['source']
    return download_url


def download_photo(photo):
    """Download a photo to the the path(global varialbe `directory`)
    :param photo: The photo information include id and title
    :type photo: dict
    """
    counter_lock = multiprocessing.Lock()
    photo_id = photo['id']
    photo_title = photo['title']
    download_url = get_photo_url(photo_id)
    photo_format = download_url.split('.')[-1]
    photo_title = photo_title + '.' + photo_format
    file_path = directory + os.sep + photo_title
    logger.info('Download %s...', photo_title.encode('utf-8'))
    resp = requests.get(download_url)
    with open(file_path, 'w') as f:
        f.write(resp.content)
        with counter_lock:
            global counter
            counter.value -= 1
        logger.info(
            'The number of pictures remaining: %s', counter.value
        )


def single_download_photos(photos):
    """Use single process to download photos

    :param photos: The photos to be downloaded
    :type photos: list of dicts
    """
    global counter
    counter = multiprocessing.Value('i', len(photos))
    for photo in photos:
        download_photo(photo)


def multiple_download_photos(photos):
    """Use multiple processes to download photos

    :param photos: The photos to be downloaded
    :type photos: list of dicts
    """
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
    """Use asynchronous I/O to download photos

    :param photos: The photos to be downloaded
    :type photos: list of dicts
    """
    try:
        assert gevent
    except NameError:
        logger.error('You need install gevent module. Aborting...')
        sys.exit(1)
    global counter
    counter = multiprocessing.Value('i', len(photos))
    jobs = [gevent.spawn(download_photo, photo) for photo in photos]
    gevent.joinall(jobs)


def init_logger():
    """Initialize the logger and set its format
    """
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    console = logging.StreamHandler(stream=sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    logger.addHandler(console)


def _parse_cli_args():
    """Parse the arguments from CLI using ArgumentParser
    :return: The arguments parsed by ArgumentParser
    :rtype: Namespace
    """
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
        default=None,
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
    parser.add_argument(
        '-u',
        help=(
            'Set your API key'
        ),
        action='store_true'
    )
    args = parser.parse_args()
    logger.debug(args)
    return args


def set_image_size_mode(s):
    """Set the quality of the images to be downloaded
    This set the global variable `image_size_mode`

    :param s: quality level, 1 is original size, 12 is smallest
    :type s: str
    """
    global image_size_mode
    image_size_mode = s


def _gevent_patch():
    """Patch the modules with gevent

    :return: Default is GEVENT. If it not supports gevent then return MULTIPROCESS
    :rtype: int
    """
    try:
        assert gevent
    except NameError:
        logger.warn('gevent not exist, fallback to multiprocess...')
        return MULTIPROCESS
    else:
        monkey.patch_all()  # Must patch before get_photos_info
        return GEVENT


def main():
    """The main procedure
    """

    init_logger()
    args = _parse_cli_args()

    if args.u:
        enter_api_key()
        return

    if args.O == GEVENT:
        args.O = _gevent_patch()

    set_image_size_mode(args.s)
    photoset_id = args.g
    global directory
    directory = args.d if args.d else photoset_id

    read_config()
    photos = get_photos_info(photoset_id)
    create_dir(directory)

    if args.O == SINGLE_PROCESS:
        single_download_photos(photos)
    elif args.O == MULTIPROCESS:
        multiple_download_photos(photos)
    elif args.O == GEVENT:
        event_download_photos(photos)
    else:
        logger.error('Unknown Error')


if __name__ == '__main__':
    main()
