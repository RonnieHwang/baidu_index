# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from pymongo import MongoClient
import sys
reload(sys)
sys.setdefaultencoding('utf8')
client = MongoClient('')
db = client.baidu_index
keyword_db = db.baidu_index_keyword_search
index_db = db.baidu_index
invalid_keyword_db = db.baidu_invalid_keyword
cookie_db = db.cookie

date_tuple = [None, None]


def get_keyword():
    return list(keyword_db.find())


def get_invalid_keyword():
    return list(invalid_keyword_db.find())


def get_finished_keyword():
    return list(index_db.aggregate([
        {
            '$match': {'date': {'$gte': date_tuple[0], '$lte': date_tuple[1]}}
        },
        {
            '$group': {'_id': '$keyword', 'sum': {'$sum': 1}}
        }])
    )


def get_cookies():
    return list(cookie_db.find({}).sort([('update_time', 1)]))


def save_invalid_word(word):
    invalid_keyword_db.update({'keyword': word}, {'$set': {'keyword': word}}, upsert=True)


def save_index(word, date, index):
    update_key = {'date': date, 'keyword': word}
    update_item = {'index': index, 'update_time': datetime.now(),
                   'date': date, 'keyword': word}
    index_db.update(update_key, {'$set': update_item}, upsert=True)


def get_today_str():
    return datetime.now().strftime('%Y-%m-%d')


def get_today():
    today_str = get_today_str()
    return datetime.strptime(today_str, '%Y-%m-%d')


def get_date_info(keyword_all_list, keyword_invalid_list):
    if len(date_tuple) == 2 and date_tuple[0] and date_tuple[1]:
        return date_tuple[0], date_tuple[1]

    result = index_db.aggregate([
        {
            '$sort': {'date': -1}
        },
        {
            '$group': {'_id': '$keyword', 'date': {'$first': '$date'}}
        }
    ])

    date_item_count_dict = {}
    for item in result:
        if item['_id'] in keyword_all_list and item['_id'] not in keyword_invalid_list:
            if date_tuple[0] is None or date_tuple[0] >= item['date']:
                print item['date'], item['_id']
                date_tuple[0] = item['date']
            date_item_count_dict[str(item['date'])] = date_item_count_dict.get(str(item['date']), 0) + 1

    print date_item_count_dict
    date_tuple[0] = date_tuple[0] + timedelta(days=1)
    date_tuple[1] = get_today() - timedelta(days=1)

    if date_tuple[1] < date_tuple[0]:
        print 'end date %s < start date %s, ERROR!' % (date_tuple[1], date_tuple[0])
        raise Exception()
    else:
        print date_tuple[0], 'to', date_tuple[1], 'start to get...'

    return date_tuple[0], date_tuple[1]