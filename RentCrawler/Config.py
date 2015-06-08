# coding=utf-8
import ConfigParser

__author__ = 'rxread'


class Config(object):
    def __init__(self, config_file_name):
        self.cf = ConfigParser.ConfigParser()
        self.cf.read(config_file_name)

        key_list = self.cf.get('common', 'key_search_word_list').split(',')
        custom_black_list = self.cf.get('common', 'custom_black_list').split(',')
        self.key_search_word_list = (key.strip() for key in key_list)
        self.custom_black_list = (key.strip() for key in custom_black_list)
        self.start_time = self.cf.get('common', 'start_time')

        self.db_file = self.cf.get('db', 'db_file_name')
        self.result_file = self.cf.get('db', 'result_file_name')

        self.douban_cookie = self.cf.get('douban', 'douban_cookie')
        self.douban_enable = self.cf.getboolean('douban', 'douban_enable')
        self.douban_sleep_time = self.cf.getfloat('douban', 'douban_sleep_time')

        self.newsmth_enable = self.cf.getboolean('newsmth', 'newsmth_enable')

        self.total_thread = self.cf.getint('thread', 'total_thread')

