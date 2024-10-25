#!/usr/bin/env python
# encoding: utf-8
import re
import datetime
import time

def time_fix(time_string):
    now_time = datetime.datetime.now()
    if '分钟前' in time_string:
        minutes = re.search(r'^(\d+)分钟', time_string).group(1)
        created_at = now_time - datetime.timedelta(minutes=int(minutes))
        return created_at.strftime('%Y-%m-%d %H:%M')

    if '小时前' in time_string:
        minutes = re.search(r'^(\d+)小时', time_string).group(1)
        created_at = now_time - datetime.timedelta(hours=int(minutes))
        return created_at.strftime('%Y-%m-%d %H:%M')

    if '今天' in time_string:
        return time_string.replace('今天', now_time.strftime('%Y-%m-%d'))

    if '刚刚' in time_string:
        return time_string.replace('刚刚', now_time.strftime('%Y-%m-%d'))

    if '月' in time_string:
        time_string = time_string.replace('月', '-').replace('日', '')
        time_string = str(now_time.year) + '-' + time_string
        return time_string

    return time_string


def parse_time(date):
    if re.match(' 刚刚 ', date):
        date = time.strftime('% Y-% m-% d % H:% M', time.localtime(time.time()))
    if re.match('d + 分钟前 ', date):
        minute = re.match('(d+)', date).group(1)
        date = time.strftime('% Y-% m-% d % H:% M', time.localtime(time.time() - float(minute) * 60))
    if re.match('d + 小时前 ', date):
        hour = re.match('(d+)', date).group(1)
        date = time.strftime('% Y-% m-% d % H:% M', time.localtime(time.time() - float(hour) * 60 * 60))
    if re.match(' 昨天.*', date):
        date = re.match(' 昨天 (.*)', date).group(1).strip()
        date = time.strftime('% Y-% m-% d', time.localtime() - 24 * 60 * 60) + ' ' + date
    if re.match('d{2}-d{2}', date):
        date = time.strftime('% Y-', time.localtime()) + date + ' 00:00'
    return date


keyword_re = re.compile('<span class="kt">|</span>|原图|<!-- 是否进行翻译 -->|')
emoji_re = re.compile('<img alt="|" src="//h5\.sinaimg(.*?)/>')
white_space_re = re.compile('<br />')
div_re = re.compile('</div>|<div>')
image_re = re.compile('<img(.*?)/>')
url_re = re.compile('<a href=(.*?)>|</a>')


def extract_weibo_content(weibo_html):
    s = weibo_html
    if '转发理由' in s:
        s = s.split('转发理由:', maxsplit=1)[1]
    if 'class="ctt">' in s:
        s = s.split('class="ctt">', maxsplit=1)[1]
    s = s.split('赞', maxsplit=1)[0]
    s = keyword_re.sub('', s)
    s = emoji_re.sub('', s)
    s = url_re.sub('', s)
    s = div_re.sub('', s)
    s = image_re.sub('', s)
    if '<span class="ct">' in s:
        s = s.split('<span class="ct">')[0]
    s = white_space_re.sub(' ', s)
    s = s.replace('\xa0', '')
    s = s.strip(':')
    s = s.strip()
    return s


def extract_comment_content(comment_html):
    s = comment_html
    if 'class="ctt">' in s:
        s = s.split('class="ctt">', maxsplit=1)[1]
    s = s.split('举报', maxsplit=1)[0]
    s = emoji_re.sub('', s)
    s = keyword_re.sub('', s)
    s = url_re.sub('', s)
    s = div_re.sub('', s)
    s = image_re.sub('', s)
    s = white_space_re.sub(' ', s)
    s = s.replace('\xa0', '')
    s = s.strip(':')
    s = s.strip()
    return s


# 10进制和62进制之间相互转化
# 用于解析微博id
ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def base62_encode(num, alphabet=ALPHABET):
    """Encode a number in Base X

    `num`: The number to encode
    `alphabet`: The alphabet to use for encoding
    """
    if (num == 0):
        return alphabet[0]
    arr = []
    base = len(alphabet)
    while num:
        rem = num % base
        num = num // base
        arr.append(alphabet[rem])
    arr.reverse()
    return ''.join(arr)


def base62_decode(string, alphabet=ALPHABET):
    """Decode a Base X encoded string into the number

    Arguments:
    - `string`: The encoded string
    - `alphabet`: The alphabet to use for encoding
    """
    base = len(alphabet)
    strlen = len(string)
    num = 0

    idx = 0
    for char in string:
        power = (strlen - (idx + 1))
        num += alphabet.index(char) * (base ** power)
        idx += 1

    return num


mid_re = re.compile("(\d{2})(\d{7})(\d{7})")


def mid_to_bid(mid):
    l = list()
    for g in mid_re.match(mid).groups():
        l.append(base62_encode(int(g)))
    return ''.join(l)


bid_re = re.compile("(\w{1})(\w{4})(\w{4})")


def bid_to_mid(bid):
    l = list()
    for g in bid_re.match(bid).groups():
        l.append(str(base62_decode(g)))
    return ''.join(l)


def del_blank(text):
    return text.replace("\u200b", "").replace("\n", "").replace("收起全文d", "").replace(" ", "").replace(u"\xa0", "")


