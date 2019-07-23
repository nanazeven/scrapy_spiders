# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class ScrapySpidersItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    collection = scrapy.Field()
    mongo_update_option = scrapy.Field()
