# -*- coding: utf-8 -*-
import json
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
from selenium import webdriver


class TimeLimitError(Exception):
    def __init__(self, value):
        Exception.__init__()
        self.value = value

    def __str__(self):
        return self.value


def handler(signum, frame):
    raise TimeLimitError('Time limit exceeded')


def get_image_links(main_keyword, link_file_path, num_requested=1000):
    """get image links with selenium
    
    Args:
        main_keyword (str): main keyword
        supplemented_keywords (list[str]): list of supplemented keywords
        link_file_path (str): path of the file to store the links
        num_requested (int, optional): maximum number of images to download
    
    Returns:
        None
    """
    number_of_scrolls = int(num_requested / 400) + 1 
    # number_of_scrolls * 400 images will be opened in the browser

    img_urls = set()
    driver = webdriver.Firefox()
    search_query = main_keyword
    url = "https://www.google.com/search?q="+search_query+"&source=lnms&tbm=isch"
    driver.get(url)
    
    for _ in range(number_of_scrolls):
        for __ in range(10):
            # multiple scrolls needed to show all 400 images
            driver.execute_script("window.scrollBy(0, 1000000)")
            time.sleep(2)
        # to load next 400 images
        time.sleep(5)
        try:
            driver.find_element_by_xpath("//input[@value='Show more results']").click()
        except Exception as e:
            print("Process-{0} reach the end of page or get the maximum number of requested images".format(main_keyword))
            break

    # imges = driver.find_elements_by_xpath('//div[@class="rg_meta"]') # not working anymore
    imges = driver.find_elements_by_xpath('//div[contains(@class,"rg_meta")]')
    for img in imges:
        img_url = json.loads(img.get_attribute('innerHTML'))["ou"]
        # img_type = json.loads(img.get_attribute('innerHTML'))["ity"]
        img_urls.add(img_url)
    print('Process-{0}, got {1} image urls so far'.format(main_keyword, len(img_urls)))
    print('Process-{0} totally get {1} images'.format(main_keyword, len(img_urls)))
    driver.quit()

    print(link_file_path)
    if not os.path.exists(os.path.dirname(link_file_path)):
        os.makedirs(os.path.dirname(link_file_path))
    with open(link_file_path, 'w') as wf:
        for url in img_urls:
            wf.write(url +'\n')
    print('Store all the links in file {0}'.format(link_file_path))
    from subprocess import call



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


def main(keywords_file='keywords.txt', *, out_folder='out', supp=''):
    keywords = open(keywords_file).readlines()
    keywords = [k.strip() for k in keywords]
    download_dir = out_folder + '/'
    link_files_dir = '{}/link_files/'.format(out_folder)
    log_dir = '{}/logs/'.format(out_folder)
    p = Pool(3)
    for keyword in keywords:
        p.apply_async(
            get_image_links,
            args=(keyword, link_files_dir + keyword))
    p.close()
    p.join()
    print('Fininsh getting all image links')
    p = Pool()
    for keyword in keywords:
        p.apply_async(
            download_with_time_limit,
            args=(link_files_dir + keyword, download_dir, log_dir))
    p.close()
    p.join()
    print('Finish downloading all images')


if __name__ == '__main__':
    run(main)
