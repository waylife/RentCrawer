# coding=utf-8
__author__ = 'rxread'

import sqlite3
import re
import sys
import time
import datetime
import os

import requests
from bs4 import BeautifulSoup

import Config


class RentCrawlerUtils(object):
    @staticmethod
    def isInBalckList(blacklist, toSearch):
        if blacklist:
            return False
        for item in blacklist:
            #decode('unicode-escape')
            if toSearch.find(item) != -1:
                return True
        return False

    @staticmethod
    def getTimeFromStr(timeStr):
        # 13:47:32或者2015-05-12或者2015-05-12 13:47:32
        if '-' in timeStr and ':' in timeStr:
            return datetime.datetime.strptime(timeStr, "%Y-%m-%d %H:%M:%S")
        elif '-' in timeStr:
            return datetime.datetime.strptime(timeStr, "%Y-%m-%d")
        elif ':' in timeStr:
            date_today = datetime.date.today();
            date = datetime.datetime.strptime(timeStr, "%H:%M:%S")
            return date.replace(year=date_today.year, month=date_today.month, day=date_today.day)
        else:
            return datetime.date.today()


class RentMain(object):
    smth_black_list = (u'黑名单', u'Re', u'警告', u'发布', u'关于', u'通知', u'审核', u'求助', u'规定', u'求租')
    douban_black_list=(u'搬家')

    newsmth_headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.65 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4,en-GB;q=0.2,zh-TW;q=0.2',
        'Connection': 'keep-alive',
        'X-Requested-With': 'XMLHttpRequest'  # important parameter,can not ignore
    }

    def __init__(self, config):
        self.config = config
        self.douban_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.81 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4,en-GB;q=0.2,zh-TW;q=0.2',
            'Connection': 'keep-alive',
            'DNT': '1',
            'HOST': 'www.douban.com',
            'Cookie': self.config.douban_cookie
        }

    def run(self):
        try:
            print "Crawler is running now."
            # creat database
            conn = sqlite3.connect(self.config.db_file)
            conn.text_factory = str
            cursor = conn.cursor()
            cursor.execute(
                'CREATE TABLE IF NOT EXISTS rent(id INTEGER PRIMARY KEY, title TEXT, url TEXT UNIQUE,itemtime timestamp, crawtime timestamp ,author TEXT, source TEXT,keyword TEXT,note TEXT)')
            cursor.close()
            start_time = RentCrawlerUtils.getTimeFromStr(self.config.start_time)
            print "searching data after date ", start_time

            cursor = conn.cursor()

            search_list = list(self.config.key_search_word_list)
            custom_black_list=list(self.config.custom_black_list)

            # New SMTH
            if self.config.newsmth_enable:
                newsmth_main_url = 'http://www.newsmth.net'
                newsmth_regex = r'<table class="board-list tiz"(?:\s|\S)*</td></tr></table>'
                #must do like this
                for keyword in search_list:
                    print '>>>>>>>>>>Search newsmth %s ...' % keyword
                    url = 'http://www.newsmth.net/nForum/s/article?ajax&au&b=HouseRent&t1=' + keyword
                    r = requests.get(url, headers=self.newsmth_headers)
                    if r.status_code == 200:
                        # print r.text
                        match = re.search(newsmth_regex, r.text)
                        if match:
                            try:
                                text = match.group(0)
                                soup = BeautifulSoup(text)
                                for tr in soup.find_all('tr')[1:]:
                                    title_element = tr.find_all(attrs={'class': 'title_9'})[0]
                                    title_text = title_element.text

                                    #exclude what in blacklist
                                    if RentCrawlerUtils.isInBalckList(custom_black_list, title_text):
                                        continue
                                    if RentCrawlerUtils.isInBalckList(self.smth_black_list, title_text):
                                        continue
                                    time_text = tr.find_all(attrs={'class': 'title_10'})[0].text  #13:47:32或者2015-05-12

                                    #data ahead of the specific date
                                    if RentCrawlerUtils.getTimeFromStr(time_text) < start_time:
                                        continue
                                    link_text = newsmth_main_url + title_element.find_all('a')[0].get('href').replace(
                                        '/nForum/article/', '/nForum/#!article/')
                                    author_text = tr.find_all(attrs={'class': 'title_12'})[0].find_all('a')[0].text
                                    try:
                                        cursor.execute(
                                            'INSERT INTO rent(id,title,url,itemtime,crawtime,author,source,keyword,note) VALUES(NULL,?,?,?,?,?,?,?,?)',
                                            [title_text, link_text, RentCrawlerUtils.getTimeFromStr(time_text),
                                             datetime.datetime.now(), author_text, keyword,
                                             'newsmth', ''])
                                        print 'add new data:', title_text, time_text, author_text, link_text, keyword
                                        #/nForum/article/HouseRent/225839 /nForum/#!article/HouseRent/225839
                                    except sqlite3.Error, e:
                                        print 'data exists:', title_text, link_text, e
                            except Exception, e:
                                print "error match table", e
                        else:
                            print "no data"
                    else:
                        print 'request url error %s -status code: %s:' % (url, r.status_code)
            else:
                print 'newsmth not enabled'
            # end newsmth

            #Douban: Beijing Rent,Beijing Rent Douban
            if self.config.douban_enable:
                print 'douban'
                douban_url = ['http://www.douban.com/group/search?group=35417&cat=1013&sort=time&q=',
                              'http://www.douban.com/group/search?group=26926&cat=1013&sort=time&q=',
                              'http://www.douban.com/group/search?group=262626&cat=1013&sort=time&q=',
                              'http://www.douban.com/group/search?group=252218&cat=1013&sort=time&q=',
                              'http://www.douban.com/group/search?group=279962&cat=1013&sort=time&q=',
                              'http://www.douban.com/group/search?group=257523&cat=1013&sort=time&q=',
                              'http://www.douban.com/group/search?group=232413&cat=1013&sort=time&q=',
                              'http://www.douban.com/group/search?group=135042&cat=1013&sort=time&q=',
                              'http://www.douban.com/group/search?group=252091&cat=1013&sort=time&q=',
                              'http://www.douban.com/group/search?group=10479&cat=1013&sort=time&q=',
                              'http://www.douban.com/group/search?group=221207&cat=1013&sort=time&q=']
                douban_url_name = (u'Douban-北京租房', u'Douban-北京租房豆瓣', u'Douban-北京无中介租房',
                                   u'Douban-北京租房专家', u'Douban-北京租房（非中介）', u'Douban-北京租房房东联盟(中介勿扰) ',
                                   u'Douban-北京租房（密探）', u'Douban-北漂爱合租（租房）', u'Douban-豆瓣♥北京♥租房',
                                   u'Douban-吃喝玩乐在北京', u'Douban-北京CBD租房')

                for i in range(len(list(douban_url))):
                    print 'start i->',i
                    for j in range(len(search_list)):
                        keyword = search_list[j]
                        print 'start i->j %s->%s %s' %(i,j,keyword)
                        print '>>>>>>>>>>Search %s  %s ...' % (douban_url_name[i].encode('utf-8'), keyword)
                        url_link = douban_url[i] + keyword
                        r = requests.get(url_link, headers=self.douban_headers)
                        if r.status_code == 200:
                            try:
                                if i==0:
                                    self.douban_headers['Cookie']=r.cookies
                                soup = BeautifulSoup(r.text)
                                table = soup.find_all(attrs={'class': 'olt'})[0]
                                for tr in table.find_all('tr'):
                                    td = tr.find_all('td')

                                    title_element = td[0].find_all('a')[0]
                                    title_text = title_element.get('title')
                                    #exclude what in blacklist
                                    if RentCrawlerUtils.isInBalckList(custom_black_list, title_text):
                                        continue
                                    if RentCrawlerUtils.isInBalckList(self.douban_black_list, title_text):
                                        continue
                                    time_text = td[1].get('title')

                                    #data ahead of the specific date
                                    if RentCrawlerUtils.getTimeFromStr(time_text) < start_time:
                                        continue
                                    link_text = title_element.get('href');

                                    reply_count = td[2].find_all('span')[0].text
                                    try:
                                        cursor.execute(
                                            'INSERT INTO rent(id,title,url,itemtime,crawtime,author,source,keyword,note) VALUES(NULL,?,?,?,?,?,?,?,?)',
                                            [title_text, link_text, RentCrawlerUtils.getTimeFromStr(time_text),
                                             datetime.datetime.now(), '', keyword,
                                             douban_url_name[i], reply_count])
                                        print 'add new data:', title_text, time_text, reply_count, link_text, keyword
                                    except sqlite3.Error, e:
                                        print 'data exists:', title_text, link_text, e
                            except Exception, e:
                                print "error match table", e
                        else:
                            print 'request url error %s -status code: %s:' % (url_link, r.status_code)
                        time.sleep(self.config.douban_sleep_time)
                        #print 'end i->',i
            else:
                print 'douban not enabled'
            #end douban

            cursor.close()

            cursor = conn.cursor()
            cursor.execute('SELECT * FROM rent ORDER BY itemtime DESC ,crawtime DESC')
            values = cursor.fetchall()

            #export to html file
            file = open(self.config.result_file, 'w')
            with file:
                file.writelines('<html><head>')
                file.writelines('<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>')
                file.writelines('<title>Rent Crawer Result</title></head><body>')
                file.writelines('<table rules=all>')
                file.writelines('<h1>' + prog_info + '</h1>')
                file.writelines(
                    '<tr><td>索引Index</td><td>标题Title</td><td>链接Link</td><td>发帖时间Page Time</td><td>抓取时间Crawl Time</td><td>作者Author</td><td>关键字Keyword</td><td>来源Source</td></tr>')
                for row in values:
                    file.write('<tr>')
                    for member in row:
                        file.write('<td>')
                        member = str(member)
                        if 'http' in member:
                            file.write('<a href="' + member + '" target="_black">' + member + '</a>')
                        else:
                            file.write(member)
                        file.write('</td>')
                    file.writelines('</tr>')
                file.writelines('</table>')
                file.writelines('</body></html>')
            cursor.close()
        except Exception, e:
            print "Error:", e.message
        finally:
            conn.commit()
            conn.close()
            print "Search Finish,Please open result.html to view result"
            # open result page
            #webbrowser.open("result.html")


'''
May 25 ,2015
Beijing, China
'''


class RentCrawler(object):
    def __init__(self):
        this_file_dir = os.path.split(os.path.realpath(__file__))[0]
        config_file_path = os.path.join(this_file_dir, 'config.ini')
        self.config = Config.Config(config_file_path)

    def run(self):
        rentmain = RentMain(self.config)
        rentmain.run()

# Main entry
if __name__ == '__main__':
    # set encoding
    reload(sys)
    sys.setdefaultencoding('utf8')
    prog_info = "Rent Crawler 1.2\nBy RxRead\nhttp://blog.zanlabs.com\n"
    print prog_info

    rentcrawler = RentCrawler()
    rentcrawler.run()

