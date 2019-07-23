# coding=utf=8

import scrapy
import json
from scrapy_spiders.items import ScrapySpidersItem
from bson import ObjectId


class Weibo_userSpider(scrapy.Spider):
    name = 'weibo_user'
    allowed_domains = ['weibo.cn', 'weibo.com']

    mongo_collection = "weibo_user_action"

    t_url = 'https://m.weibo.cn/api/container/getIndex?uid={}&type=uid&value={}'
    target_user = []
    start_urls = [t_url.format(uid, uid) for uid in target_user]

    repost_url = 'https://m.weibo.cn/api/statuses/repostTimeline?id={}&page={}'
    comment_url = 'https://m.weibo.cn/api/comments/show?id={}&page={}'
    attitudes_url = 'https://m.weibo.cn/api/attitudes/show?id={}&page={}'

    custom_settings = {
        'CONCURRENT_REQUESTS': 8,
        'DOWNLOAD_DELAY': 1,
        'COOKIES_ENABLED': False,
        'LOG_LEVEL': 'INFO',
        'RETRY_TIMES': 15,
        'USER_AGENT': "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/55.0.2883.75 Safari/537.36 Maxthon/5.1.3.2000",

        'REDIS_HOST': '127.0.0.1',
        'REDIS_PORT': '6389',
        'REDIS_DB': '0',
        'MONGO_URL': 'mongodb://127.0.0.1:27017',
        'MONGO_DB': name,
        'ITEM_PIPELINES': {
            'scrapy_spiders.WeiboPipeline': 399,
        },
        'DOWNLOADER_MIDDLEWARES': {
            # 'scrapy_spiders.middlewares.ProxyMiddleware': 499,
        },
    }

    def parse(self, response):
        data = json.loads(response.text)
        if data['ok'] != 1:
            return
        statuses_count = data['data']['userInfo']['statuses_count']
        followers_count = data['data']['userInfo']['followers_count']
        follow_count = data['data']['userInfo']['follow_count']
        containerid = data['data']['tabsInfo']['tabs'][1]['containerid']
        for i in range(1, int(statuses_count // 10)):
            url = f'https://m.weibo.cn/api/container/getIndex?containerid={containerid}&page={i}'
            yield scrapy.Request(url, self.parse_page)

    def parse_page(self, response):
        data = json.loads(response.text)
        if data['ok'] != 1:
            return

        for c in data['data']['cards']:
            weibo_id = c['mblog'].get('id')

            # 查询转发用户
            url = self.repost_url.format(weibo_id, 1)
            yield scrapy.Request(url, self.parse_repost, meta={'weibo_id': weibo_id, 'page': 'first'})

            # 查询评论用户
            url = self.comment_url.format(weibo_id, 1)
            yield scrapy.Request(url, self.parse_comment, meta={'weibo_id': weibo_id, 'page': 'first'})

            # 查询点赞用户
            url = self.attitudes_url.format(weibo_id, 1)
            yield scrapy.Request(url, self.parse_attitudes, meta={'weibo_id': weibo_id, 'page': 'first'})

    def parse_repost(self, response):
        data = json.loads(response.text)
        if data['ok'] != 1:
            return

        weibo_id = response.meta['weibo_id']

        # 对第一页需要提取总数 特殊处理
        if response.meta['page'] == 'first':
            total_number = data['data'].get('total_number')
            page_size = 50
            for i in range(1, int(total_number // page_size)):
                url = self.repost_url.format(weibo_id, i)
                yield scrapy.Request(url, self.parse_repost, meta={'weibo_id': weibo_id, 'page': i})
            return

        for i in data['data']['data']:
            user = dict()
            user['id'] = i['user']['id']
            user['statuses_count'] = i['user']['statuses_count']
            user['screen_name'] = i['user']['screen_name']
            user['profile_url'] = i['user']['profile_url']
            user['description'] = i['user']['description']
            user['gender'] = i['user']['gender']
            user['followers_count'] = i['user']['followers_count']
            user['follow_count'] = i['user']['follow_count']

            action_item = ScrapySpidersItem()
            action_item['collection'] = self.mongo_collection
            action_item['mongo_update_option'] = {
                'filter': {"_id": ObjectId()},
                "update": {"$set": user},
                "upsert": True
            }
            yield action_item

    def parse_comment(self, response):
        data = json.loads(response.text)
        if data['ok'] != 1:
            return

    def parse_attitudes(self, response):
        data = json.loads(response.text)
        if data['ok'] != 1:
            return
