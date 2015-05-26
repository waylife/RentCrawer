# Rent Crawer 租房爬虫
This is a house rental information crawler project for people living in Beijing.
Currently no other language documents are available.  

------

##介绍
适用人群：北京,有一定程序基础人群  

最近为了抓取个人房东的出租信息，写了一个爬虫，用来整合水木清华租房版，以及豆瓣北京租房小组里面相关的租房信息，方便自己查看信息，不用每次都去搜索相关内容

> * 可以配置租房区域
> * 可以配置黑名单
> * 可以配置帖子开始时间

抓取结果示意图：
![Rent Crawer Result](https://github.com/waylife/RentCrawer/blob/master/Images/result_1.0.png?raw=true)

##使用说明
1. 【必须】配置RentCrawler.py中52行key_search_word字段为你先搜索的区域
2. 【必须】配置RentCrawler.py中53行custom_black_list字段为你不想搜到的内容
3. 【必须】配置RentCrawler.py中54行start_time_str字段为帖子开始时间
4. 【可选】删除rentdata.db以及result.html文件，如果不希望本次结果与上次混合在一起，可以删除相关文件
5. 【必须】运行RentCrawler.py文件
6. 【必须】程序结束后打开result.html查看结果
