# -*- coding: utf-8 -*-
import time
import requests
import keyword_generator
import mongo_util
from multi_thread import *
from Queue import Queue
from datetime import datetime
from datetime import timedelta

cookie_queue = Queue()
keyword_queue = Queue()

MAX_BURST = 10  # Depends on your proxies and cookies
MAX_TASK_CNT = 100  # How many keywords to fetch of every cookie
TASK_INTERVAL = 2  # Seconds to wait after fetch one keyword


class RequestResult:
    SUCCESS = 'Success    '  # got data
    ERROR_BAD_REQUEST = 'Bad Request'  # server status, not worth retry.
    ERROR_NOT_LOGIN = 'Not Login  '  # server status, cookie invalid, not worth retry.
    FAILED = 'Failed     '  # request failed, worth retry.

    def __init__(self, message):
        self.message = message
        self.indexes = None
        self.start_date = None
        self.end_date = None

    def set_data(self, indexes=None, start_date=None, end_date=None):
        self.indexes = indexes
        self.start_date = start_date
        self.end_date = end_date
        if self.indexes is None:
            self.message = self.FAILED

    def is_success(self):
        return self.message == self.SUCCESS


class RequestIndex:
    header = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36',
        'Accept-Encoding': 'gzip,deflate'
    }

    index_url = 'http://index.baidu.com/api/SearchApi/index?area=0&word=%s&startDate=%s&endDate=%s'
    ptbk_url = 'http://index.baidu.com/Interface/ptbk?uniqid=%s'

    session = requests.Session()
    session.proxies = {'http': 'http://127.0.0.1:6666',
                       'https': 'http://127.0.0.1:6666', }
    session.trust_env = False

    def get_cookie_str(self, cookies):
        return '; '.join(['%s=%s' % (item['name'], item['value'])
                          for item in cookies])

    def decrypt(self, ptbk, indexes):
        try:
            n = {}
            s = ''
            for o in range(0, len(ptbk) / 2):
                n[ptbk[o]] = ptbk[len(ptbk) / 2 + o]
            for r in range(len(indexes)):
                s += n[indexes[r]]
            return s
        except KeyError:
            return None

    def __init__(self, cookie_item, date_tuple):
        self.cookie_item = cookie_item
        self.start_date = date_tuple[0].strftime('%Y-%m-%d')
        self.end_date = date_tuple[1].strftime('%Y-%m-%d')
        self.header.update({'Cookie': self.get_cookie_str(cookie_item['cookie'])})

    def check_response(self, keyword, response):
        if response.status_code != 200:
            return RequestResult(message=RequestResult.FAILED)

        if 'data' in response.json().keys():
            if response.json()['data'] == '':
                if 'message' in response.json().keys():
                    if response.json()['message'] == 'bad request':
                        return RequestResult(message=RequestResult.ERROR_BAD_REQUEST)
                    elif response.json()['message'] == 'not login':
                        return RequestResult(message=RequestResult.ERROR_NOT_LOGIN)
                print 'Unknown Error:', keyword, self.cookie_item['username'], response.content
                return RequestResult(message=RequestResult.FAILED)
        else:
            return RequestResult(message=RequestResult.FAILED)
            print 'Unknown Error:', keyword, self.cookie_item['username'], response.content
        return RequestResult(message=RequestResult.SUCCESS)

    def fetch_index(self, keyword):
        """
        :param keyword: keyword to fetch indexes
        :return: list of indexes, start date and end date which get from server
        """
        response = self.session.get(url=self.index_url % (keyword.decode('utf-8'), self.start_date, self.end_date),
                                    headers=self.header)
        request_result = self.check_response(keyword, response)
        if not request_result.is_success():
            return request_result

        uniqid = response.json()['data']['uniqid']
        index_all = response.json()['data']['userIndexes'][0]['all']

        response = self.session.get(url=self.ptbk_url % uniqid, headers=self.header)
        request_result = self.check_response(keyword, response)

        if not request_result.is_success():
            return request_result

        ptbk = response.json()['data']
        start_date = index_all['startDate']
        end_date = index_all['endDate']
        request_result.set_data(self.decrypt(ptbk, index_all['data']), start_date, end_date)
        return request_result


def generate_cookie():
    for item in mongo_util.get_cookies():
        cookie_queue.put(item)


def get_index(cooke_item):
    request_index = RequestIndex(cooke_item, mongo_util.date_tuple)
    while not keyword_queue.empty():
        keyword = keyword_queue.get()
        result = request_index.fetch_index(keyword)

        print result.message, keyword, cooke_item['username'], result.start_date, 'to', result.end_date, result.indexes

        if result.is_success():
            process_result = process_data(keyword, result.indexes, result.start_date, result.end_date)
            if not process_result:
                keyword_queue.put(keyword)
        elif result.message == RequestResult.FAILED:
            keyword_queue.put(keyword)
        elif result.message == RequestResult.ERROR_BAD_REQUEST:
            # mongo_util.save_invalid_word(keyword) # consider to put this keyword into invalid set.
            pass
        elif result.message == RequestResult.ERROR_NOT_LOGIN:
            keyword_queue.put(keyword)
            break
        time.sleep(TASK_INTERVAL)


def process_data(keyword, data, start_date, end_date):
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')

    date = start_date
    index_list = data.split(',')
    if (end_date - start_date).days + 1 != len(index_list):
        print 'Process Error, dates and indexes not match！'
        return False

    for index in index_list:
        if index == '':
            index = 0
        else:
            index = int(index)
        # print keyword, date, index
        mongo_util.save_index(keyword, date, index)
        date += timedelta(days=1)
    return True


def main():
    keyword_generator.generate_task_queue(keyword_queue)
    print 'Total tasks:', keyword_queue.qsize()
    generate_cookie()
    wm = WorkManager(MAX_BURST)

    while not cookie_queue.empty():
        cooke_item = cookie_queue.get()
        wm.add_job(cooke_item, get_index, cooke_item)

    wm.start()
    wm.wait_for_complete()


def test_main(burst=1):
    global MAX_BURST
    MAX_BURST = burst
    mongo_util.date_tuple = (datetime(2018, 10, 10), datetime(2018, 11, 11))
    keyword_queue.put('iphone')
    keyword_queue.put('xsxsxsxsxs')
    for cookie_item in mongo_util.get_cookies():
        get_index(cookie_item)


if __name__ == '__main__':
    main()
    # test_main(3)
