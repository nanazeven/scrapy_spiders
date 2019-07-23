import scrapy
import re
from scrapy import Selector
from scrapy_redis.spiders import RedisSpider

class ComicSpider(RedisSpider):
    name = 'comic'