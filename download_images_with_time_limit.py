# -*- coding: utf-8 -*-
import os
import time
import signal
import logging
import urllib.request
import urllib.error
from urllib.parse import urlparse
from multiprocessing import Pool

from user_agent import generate_user_agent
from clize import run


class TimeLimitError(Exception):
    def __init__(self, value):
        Exception.__init__()
        self.value = value

    def __str__(self):
        return self.value


def handler(signum, frame):
    raise TimeLimitError('Time limit exceeded')


def download_with_time_limit(
        link_file_path,
        download_dir,
        log_dir,
        limit_time=10):
    main_keyword = link_file_path.split('/')[-1]
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_file = log_dir + 'download_selenium_{0}.log'.format(main_keyword)
    logging.basicConfig(
        level=logging.DEBUG,
        filename=log_file,
        filemode="a+",
        format="%(asctime)-15s %(levelname)-8s  %(message)s")
    folder = main_keyword.replace(' ', '_')
    img_dir = download_dir + folder + '/'
    count = 0
    headers = {}
    if not os.path.exists(img_dir):
        os.makedirs(img_dir)
    signal.signal(signal.SIGALRM, handler)
    with open(link_file_path, 'r') as rf:
        for link in rf:
            try:
                ref = 'https://www.google.com'
                o = urlparse(link)
                ref = o.scheme + '://' + o.hostname
                ua = generate_user_agent()
                headers['User-Agent'] = ua
                headers['referer'] = ref
                try:
                    signal.alarm(limit_time)
                    req = urllib.request.Request(link.strip(), headers=headers)
                    response = urllib.request.urlopen(req)
                    data = response.read()
                except TimeLimitError as e:
                    print('TimeLimitError: process-{0} encounters {1}'.format(main_keyword, e.value))
                    logging.error('TimeLimitError while downloading image{0}'.format(link))
                    continue
                finally:
                    signal.alarm(0)

                file_path = img_dir + '{0}.jpg'.format(count)
                with open(file_path,'wb') as wf:
                    wf.write(data)
                print('Process-{0} download image {1}/{2}.jpg'.format(main_keyword, main_keyword, count))
                count += 1
                if count % 10 == 0:
                    print('Process-{0} is sleeping'.format(main_keyword))
                    time.sleep(5)
            except urllib.error.HTTPError as e:
                print('HTTPError')
                logging.error('HTTPError while downloading image {0}http code {1}, reason:{2}'.format(link, e.code, e.reason))
                continue
            except urllib.error.URLError as e:
                print('URLError')
                logging.error('URLError while downloading image {0}reason:{1}'.format(link, e.reason))
                continue
            except Exception as e:
                print('Unexpected Error')
                logging.error('Unexpeted error while downloading image {0}error type:{1}, args:{2}'.format(link, type(e), e.args))
                continue


def main(keywords_file='keywords.txt', out_folder='out', supp=''):
    keywords = open(keywords_file).readlines()
    keywords = [k.strip() for k in keywords]
    main_keywords = keywords
    download_dir = '{}/data_limit_time/'.format(out_folder)
    link_files_dir = '{}/data/link_files/'.format(out_folder)
    log_dir = '{}/logs_limit_time/'.format(out_folder)
    p = Pool()
    for keyword in main_keywords:
        p.apply_async(
            download_with_time_limit,
            args=(link_files_dir + keyword, download_dir, log_dir))
    p.close()
    p.join()
    print('Finish downloading all images')


if __name__ == '__main__':
    run(main)
