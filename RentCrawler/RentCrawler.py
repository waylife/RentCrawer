# coding=utf-8
__author__ = 'rxread'

import sqlite3
import re
import sys
import time
import datetime
import webbrowser

import requests
from bs4 import BeautifulSoup


class getoutofloop(Exception): pass


def isInBalckList(blacklist, toSearch):
    for item in blacklist:
        if toSearch.find(item) != -1:
            return True;
    return False


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



'''
May 25 ,2015
Beijing, China
'''

# set encoding
reload(sys)
sys.setdefaultencoding('utf8')
prog_info = "Rent Crawler 1.1\nBy RxRead\nhttp://blog.zanlabs.com\n"
print prog_info


#######################################
#You can modify configurations below
key_search_word = (u'三元桥',u'国贸',u'回龙观')
custom_black_list = (u'隔断', u'单间', u'一居室')
start_time_str = '2015-03-12'
#You can modify configurations above
######################################

smth_black_list = (u'黑名单', u'Re', u'警告', u'发布', u'关于', u'通知', u'审核', u'求助', u'规定', u'求租')

newsmth_headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.65 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4,en-GB;q=0.2,zh-TW;q=0.2',
    'Connection': 'keep-alive',
    'X-Requested-With': 'XMLHttpRequest'  #important parameter,can not ignore
}

douban_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.81 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, sdch',
    'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4,en-GB;q=0.2,zh-TW;q=0.2',
    'Connection': 'keep-alive',
    'DNT': '1',
    'HOST': 'www.douban.com',
    'Cookie': 'bid="aszzdddsw"; ue="usyhhs@qq.com"; ll="10822388"; _pk_ref.100001.8cb4=%5B%22%22%2C%22%22%2C1432697511%2C%22https%3A%2F%2Fwww.baidu.com%2Flink%3Furl%3D7gqnBpvJdRVNXiY3uz6NC8MakeEiO9sJ5MkSPCVt1_5XtHvTf9hnUt8ZpUIThjOz%26wd%3D%25E8%25B1%2586%25E7%2593%25A3%25E5%258C%2597%25E4%25BA%25AC%25E7%25A7%259F%25E6%2588%25BF%2520%25E5%25B8%2596%25E5%25AD%2590%2520%25E8%2587%25AA%25E5%258A%25A8%25E6%258A%2593%25E5%258F%2596%26issp%3D1%26f%3D8%26ie%3Dutf-8%26tn%3Dbaiduhome_pg%26inputT%3D5816%22%5D; ps=y; __utmt=1; dbcl2="68564289:Us+tdIIhfuI"; ck="oNkx"; ap=1; push_noty_num=0; push_doumail_num=0; _pk_id.100001.8cb4=c8a8b67bc01d90d4.1428030074.12.1432699611.1432695397.; _pk_ses.100001.8cb4=*; __utma=20149791.251340141.1428030075.14321694682.1432697511.13; __utmb=20149791.26.10.1432697511; __utmc=20149791; __utmz=20149791.1432535587.8.5.utmcsr=baidu|utmccn=(organic)|utmcmd=organic|utmctr=%E8%B1%86%E7%93%A3%E5%8C%97%E4%BA%AC%E7%A7%9F%E6%88%BF%20%E5%B8%96%E5%AD%90%20%E8%87%AA%E5%8A%A8%E6%8A%93%E5%8F%96; __utmv=20149791.6856'
}

smth_switch=True;
douban_siwtch=True;


try:
    print "Crawler is running now."
    # creat database
    conn = sqlite3.connect('rentdata.db')
    conn.text_factory=str
    cursor = conn.cursor()
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS rent(id INTEGER PRIMARY KEY, title TEXT, url TEXT UNIQUE,itemtime timestamp, crawtime timestamp ,author TEXT, source TEXT,keyword TEXT,note TEXT)')
    cursor.close()
    start_time = getTimeFromStr(start_time_str)
    print "searching data after date ", start_time

    cursor = conn.cursor()
    #New SMTH
    if smth_switch:
        newsmth_main_url = 'http://www.newsmth.net'
        newsmth_regex = r'<table class="board-list tiz"(?:\s|\S)*</td></tr></table>'
        for keyword in key_search_word:
            print '>>>>>>>>>>Search newsmth %s ...' % keyword
            url = 'http://www.newsmth.net/nForum/s/article?ajax&au&b=HouseRent&t1=' + keyword
            r = requests.get(url, headers=newsmth_headers)
            if r.status_code == 200:
                #print r.text
                match = re.search(newsmth_regex, r.text)
                if match:
                    try:
                        text = match.group(0)
                        soup = BeautifulSoup(text)
                        for tr in soup.find_all('tr')[1:]:
                            title_element = tr.find_all(attrs={'class': 'title_9'})[0]
                            title_text = title_element.text

                            #exclude what in blacklist
                            if isInBalckList(custom_black_list, title_text):
                                continue
                            if isInBalckList(smth_black_list, title_text):
                                continue
                            time_text = tr.find_all(attrs={'class': 'title_10'})[0].text  #13:47:32或者2015-05-12

                            #data ahead of the specific date
                            if getTimeFromStr(time_text) < start_time:
                                continue
                            link_text = newsmth_main_url + title_element.find_all('a')[0].get('href').replace(
                                '/nForum/article/', '/nForum/#!article/')
                            author_text = tr.find_all(attrs={'class': 'title_12'})[0].find_all('a')[0].text
                            try:
                                cursor.execute(
                                    'INSERT INTO rent(id,title,url,itemtime,crawtime,author,source,keyword,note) VALUES(NULL,?,?,?,?,?,?,?,?)',
                                    [title_text, link_text, getTimeFromStr(time_text), datetime.datetime.now(), author_text,keyword,
                                     'newsmth', ''])
                                print 'add new data:', title_text, time_text, author_text, link_text,keyword
                                #/nForum/article/HouseRent/225839 /nForum/#!article/HouseRent/225839
                            except sqlite3.Error, e:
                                print 'data exists:',title_text,link_text,e
                    except Exception, e:
                        print "error match table", e
                else:
                    print "no data"
            else:
                print 'request url error %s -status code: %s:' %(url,r.status_code)
    #end newsmth

    #Douban: Beijing Rent,Beijing Rent Douban
    if douban_siwtch:
        douban_url = ('http://www.douban.com/group/search?group=35417&cat=1013&q=',
                      'http://www.douban.com/group/search?group=26926&cat=1013&q=',
                      'http://www.douban.com/group/search?group=262626&cat=1013&q=',
                      'http://www.douban.com/group/search?group=252218&cat=1013&q=',
                      'http://www.douban.com/group/search?group=279962&cat=1013&q=',
                      'http://www.douban.com/group/search?group=257523&cat=1013&q=',
                      'http://www.douban.com/group/search?group=232413&cat=1013&q=',
                      'http://www.douban.com/group/search?group=135042&cat=1013&q=',
                      'http://www.douban.com/group/search?group=252091&cat=1013&q=',
                      'http://www.douban.com/group/search?group=10479&cat=1013&q=',
                      'http://www.douban.com/group/search?group=221207&cat=1013&q=')
        douban_url_name=(u'Douban-北京租房',u'Douban-北京租房豆瓣',u'Douban-北京无中介租房',
                         u'Douban-北京租房专家',u'Douban-北京租房（非中介）',u'Douban-北京租房房东联盟(中介勿扰) ',
                         u'Douban-北京租房（密探）',u'Douban-北漂爱合租（租房）',u'Douban-豆瓣♥北京♥租房',
                         u'Douban-吃喝玩乐在北京',u'Douban-北京CBD租房')
        douban_url_index=0
        for url in douban_url:
            for keyword in key_search_word:
                print '>>>>>>>>>>Search %s  %s ...' % (douban_url_name[douban_url_index],keyword)
                url_link = url + keyword
                r = requests.get(url_link, headers=douban_headers)
                if r.status_code == 200:
                    try:
                        soup = BeautifulSoup(r.text)
                        table = soup.find_all(attrs={'class': 'olt'})[0]
                        for tr in table.find_all('tr'):
                            td = tr.find_all('td')

                            title_element=td[0].find_all('a')[0]
                            title_text = title_element.get('title')

                            #exclude what in blacklist
                            if isInBalckList(custom_black_list, title_text):
                                continue
                            if isInBalckList(smth_black_list, title_text):
                                continue
                            time_text = td[1].get('title')

                            #data ahead of the specific date
                            if getTimeFromStr(time_text) < start_time:
                                continue
                            link_text = title_element.get('href');

                            reply_count=td[2].find_all('span')[0].text
                            try:
                                cursor.execute(
                                    'INSERT INTO rent(id,title,url,itemtime,crawtime,author,source,keyword,note) VALUES(NULL,?,?,?,?,?,?,?,?)',
                                    [title_text, link_text, getTimeFromStr(time_text), datetime.datetime.now(), '',keyword,
                                     douban_url_name[douban_url_index],reply_count])
                                print 'add new data:',title_text, time_text, reply_count,link_text,keyword
                            except sqlite3.Error, e:
                                print 'data exists:',title_text,link_text,e
                    except Exception, e:
                        print "error match table", e
                else:
                    print 'request url error %s -status code: %s:' %(url_link,r.status_code)
                time.sleep(1)
            douban_url_index+=1
    #end douban

    cursor.close()

    # conn.commit()
    # cursor.close()
    # export database data to txt file
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM rent ORDER BY itemtime DESC ,crawtime DESC')
    values = cursor.fetchall()

    #export to html file
    file = open('result.html', 'w')
    with file:
        file.writelines('<html><head>')
        file.writelines('<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>')
        file.writelines('<title>Rent Crawer Result</title></head><body>')
        file.writelines('<table rules=all>')
        file.writelines('<h1>' + prog_info + '</h1>')
        file.writelines('<tr><td>索引Index</td><td>标题Title</td><td>链接Link</td><td>发帖时间Page Time</td><td>抓取时间Crawl Time</td><td>作者Author</td><td>关键字Keyword</td><td>来源Source</td></tr>')
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
    print "Error:", e
finally:
    conn.commit()
    conn.close()
    print "Search Finish,Please open result.html to view result"
    #open result page
    #webbrowser.open("result.html")
