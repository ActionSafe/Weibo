#!/usr/bin/env python
# encoding: utf-8
import re
from scrapy.spiders import Spider
from scrapy.crawler import CrawlerProcess
from scrapy.selector import Selector
from scrapy.http import Request
from scrapy.utils.project import get_project_settings
from scrapy_redis.spiders import RedisSpider
from sina.items import TweetsItem, InformationItem
from sina.spiders.utils import time_fix, mid_to_bid, del_blank
import time
from sina.settings import KEYWORD, API, SORT


class WeiboSpider(RedisSpider):
    name = "weibo_spider"
    base_url = "https://weibo.cn"
    redis_key = "weibo_spider:start_urls"
    search_api = "https://s.weibo.com"

    # 速度太快大概率被封禁
    custom_settings = {
        'CONCURRENT_REQUESTS': 16,
        "DOWNLOAD_DELAY": 0.1,
    }

    def parse(self, response):
        # 判断有没有找到相关结果
        if response.selector.xpath("//div[contains(@class,'card-no-result')]"):
            self.logger.error("没有找到相关结果:" + response.url)
            return None

        # 获取当前页码指针
        cur = response.selector.xpath("//div[@class='m-page']//li[@class='cur']//text()").extract_first()
        # 判断是不是第1页
        if cur:
            if "第1页" in cur:
                for link in response.selector.xpath("//div[@class='m-page']//li/a/@href").extract():
                    yield Request(self.search_api + link, callback=self.parse)

        # 解析微博卡片
        for card in response.selector.xpath("//div[@class='m-con-l']//div[@class='card-wrap']"):
            try:
                tweet_item = TweetsItem()
                current_time = int(time.time())
                tweet_item['crawl_time'] = current_time
                content = card.xpath(".//div[@class='content']")[0]
                info = content.xpath(".//div[@class='info']")[0]
                uid = info.xpath(".//a[@class='name']/@href").re_first(r"//weibo.com/(\d+)?")
                tweet_item['user_id'] = uid
                tweet_item['_id'] = uid + "_" + mid_to_bid(card.xpath("./@mid").extract_first())
                source = content.xpath("./p[@class='from']/a/text()").extract()
                tweet_item['created_at'] = time_fix(source[0].strip())
                tweet_item['tool'] = source[1] if len(source) > 1 else None
                tweet_item['content'] = self.parse_content(content)
                origin = content.xpath(".//div[@node-type='feed_list_forwardContent']")
                if origin:
                    tweet_item['origin_weibo_content'] = self.parse_content(origin)
                    tweet_item['origin_weibo'] = "https:"+content.xpath(".//div[@class='func']//li//a/@href").extract_first()
                actions = card.xpath(".//div[@class='card-act']//li")
                tweet_item['repost_num'] = int(actions[1].xpath("./a/text()").re_first(r"(\d+)", default=0))
                tweet_item['comment_num'] = int(actions[2].xpath("./a/text()").re_first(r"(\d+)", default=0))
                tweet_item['like_num'] = int(actions[3].xpath("./a//text()").re_first(r"(\d+)", default=0))
                tweet_item['keyword'] = KEYWORD
                tweet_item['API'] = API
                tweet_item['sort'] = SORT
                yield tweet_item
            except Exception as e:
                self.logger.error(e)
                continue

            # yield Request(url_cn="https://weibo.cn/{}/info".format(tweet_item['user_id']),
            #               callback=self.parse_information, priority=2)

    def parse_content(self, content):
        text = content.xpath("./p[@class='txt' and @node-type='feed_list_content_full']//text()")
        if text:
            l = map(lambda x: x.strip(), text.extract())
            weibo = ''.join(l)
        else:
            text = content.xpath("./p[@class='txt' and @node-type='feed_list_content']//text()")
            l = map(lambda x: x.strip(), text.extract())
            weibo = ''.join(l)
        # 去掉空白字符、特殊字符
        return del_blank(weibo)


    # 这里用旧的微博接口进行个人信息的抓取
    def parse_information(self, response):
        """ 抓取个人信息 """
        information_item = InformationItem()
        information_item['crawl_time'] = int(time.time())
        selector = Selector(response)
        information_item['_id'] = re.findall('(\d+)/info', response.url)[0]
        text1 = ";".join(selector.xpath('body/div[@class="c"]//text()').extract())  # 获取标签里的所有text()
        nick_name = re.findall('昵称;?[：:]?(.*?);', text1)
        gender = re.findall('性别;?[：:]?(.*?);', text1)
        place = re.findall('地区;?[：:]?(.*?);', text1)
        briefIntroduction = re.findall('简介;?[：:]?(.*?);', text1)
        # birthday = re.findall('生日;?[：:]?(.*?);', text1)
        # sex_orientation = re.findall('性取向;?[：:]?(.*?);', text1)
        # sentiment = re.findall('感情状况;?[：:]?(.*?);', text1)
        # vip_level = re.findall('会员等级;?[：:]?(.*?);', text1)
        authentication = re.findall('认证;?[：:]?(.*?);', text1)
        labels = re.findall('标签;?[：:]?(.*?)更多>>', text1)
        if nick_name and nick_name[0]:
            information_item["nick_name"] = nick_name[0].replace(u"\xa0", "")
        if gender and gender[0]:
            information_item["gender"] = gender[0].replace(u"\xa0", "")
        if place and place[0]:
            place = place[0].replace(u"\xa0", "").split(" ")
            information_item["province"] = place[0]
            if len(place) > 1:
                information_item["city"] = place[1]
        if briefIntroduction and briefIntroduction[0]:
            information_item["brief_introduction"] = briefIntroduction[0].replace(u"\xa0", "")
        # if birthday and birthday[0]:
        #     information_item['birthday'] = birthday[0]
        # if sex_orientation and sex_orientation[0]:
        #     if sex_orientation[0].replace(u"\xa0", "") == gender[0]:
        #         information_item["sex_orientation"] = "同性恋"
        #     else:
        #         information_item["sex_orientation"] = "异性恋"
        # if sentiment and sentiment[0]:
        #     information_item["sentiment"] = sentiment[0].replace(u"\xa0", "")
        # if vip_level and vip_level[0]:
        #     information_item["vip_level"] = vip_level[0].replace(u"\xa0", "")
        if authentication and authentication[0]:
            information_item["authentication"] = authentication[0].replace(u"\xa0", "")
        if labels and labels[0]:
            information_item["labels"] = labels[0].replace(u"\xa0", ",").replace(';', '').strip(',')
        request_meta = response.meta
        request_meta['item'] = information_item
        yield Request(self.base_url + '/u/{}'.format(information_item['_id']),
                      callback=self.parse_further_information,
                      meta=request_meta, dont_filter=True, priority=1)

    def parse_further_information(self, response):
        text = response.text
        information_item = response.meta['item']
        tweets_num = re.findall('微博\[(\d+)\]', text)
        if tweets_num:
            information_item['tweets_num'] = int(tweets_num[0])
        follows_num = re.findall('关注\[(\d+)\]', text)
        if follows_num:
            information_item['follows_num'] = int(follows_num[0])
        fans_num = re.findall('粉丝\[(\d+)\]', text)
        if fans_num:
            information_item['fans_num'] = int(fans_num[0])
        yield information_item


if __name__ == "__main__":
    process = CrawlerProcess(get_project_settings())
    process.crawl('weibo_spider')
    process.start()
