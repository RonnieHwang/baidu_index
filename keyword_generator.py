# -*- coding: utf-8 -*-
import mongo_util

keyword_all_list = []
keyword_invalid_list = []
keyword_finished_list = []


def generate_all_list():
    for item in mongo_util.get_keyword():
        keyword = item['keyword'].encode('utf-8').strip()
        keyword_all_list.append(keyword)


def generate_invalid_list():
    for item in mongo_util.get_invalid_keyword():
        keyword_invalid_list.append(item['keyword'].encode('utf-8'))


def generate_finished_list():
    start_date, end_date = mongo_util.get_date_info(keyword_all_list, keyword_invalid_list)
    days_diff = (end_date - start_date).days

    for item in mongo_util.get_finished_keyword():
        if item['sum'] > days_diff:
            keyword_finished_list.append(item['_id'].encode('utf-8'))

    print 'Total:', len(keyword_all_list), 'days:', days_diff, 'from:', start_date, 'to:', end_date
    print 'Invalid:', len(keyword_invalid_list)
    print 'Already got:', len(keyword_finished_list)


def generate_task_queue(keyword_queue):
    generate_all_list()
    generate_invalid_list()
    generate_finished_list()
    for keyword in keyword_all_list:
        if keyword in keyword_finished_list or keyword in keyword_invalid_list:
            continue
        keyword_queue.put(keyword)

