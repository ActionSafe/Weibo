#!/usr/bin/env python
# encoding: utf-8
import redis
import sys
import os
import datetime
sys.path.append(os.getcwd())
from sina.settings import LOCAL_REDIS_HOST, LOCAL_REDIS_PORT, KEYWORD, SORT


r = redis.Redis(host=LOCAL_REDIS_HOST, port=LOCAL_REDIS_PORT)

# 循环扫描之前的链接信息并删除
for key in r.scan_iter("weibo_spider*"):
    r.delete(key)
    print('删除成功')

# 新浪微博高级搜索接口
# 接口说明:
# q="" => 查询关键字
# xsort="hot" => 指定按热度排序
# scope="ori" => 指定原创微博
# vip=1 => 指定为认证用户
# category=4 => 指定为认证媒体发布的微博
# timescope=custom:2020-02-29-23:2020-03-01-00 指定检索的时间范围
if SORT == 'time':
    url_format = "https://s.weibo.com/weibo?q={}&typeall=1&suball=1&timescope=custom:{}:{}"
else:
    url_format = "https://s.weibo.com/weibo?q={}&xsort=hot&typeall=1&suball=1&timescope=custom:{}:{}"
# url_format = "https://weibo.cn/search/mblog?hideSearchFrame=&keyword={}&advancedfilter=1&starttime={}&endtime={}&sort=time&page=1"
# 搜索的关键词，可以修改
keyword = KEYWORD
# 搜索的起始日期，可修改 微博的创建日期是2009-08-16 也就是说不要采用这个日期更前面的日期了
date_start = datetime.datetime.strptime("2020-05-25-0", '%Y-%m-%d-%H')
# 搜索的结束日期，可修改
date_end = datetime.datetime.strptime("2020-07-16-0", '%Y-%m-%d-%H')
# 时间间隔
time_spread = datetime.timedelta(hours=1)


while date_start < date_end:
    next_time = date_start + time_spread
    url = url_format.format(keyword, date_start.strftime("%Y-%m-%d-%H"), next_time.strftime("%Y-%m-%d-%H"))
    r.lpush('weibo_spider:start_urls', url)
    date_start = next_time
    print('添加{}成功'.format(url))
