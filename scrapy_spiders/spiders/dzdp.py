# -*- coding: utf-8 -*-
import scrapy


class DzdpSpider(scrapy.Spider):
    name = 'dzdp'
    allowed_domains = ['www.dianping.com']

    start_urls = ['http://www.dianping.com/beijing/ch10/r14o2']

    # def start_requests(self):
    #     yield scrapy.Request("http://www.dianping.com/beijing/ch10/r14/o2", self.parse,
    #                          cookies={"s_ViewType": "10", "_hc.v": "afd64d03-a5ba-ce2f-c8a3-0e059e2a151d.1560716891"})

    def parse(self, response):
        item = {}
        li_list = response.xpath("//div[@id='shop-all-list']/ul/li")
        for li in li_list:
            item['pic_url'] = li.xpath("./div[@calss='pic']/a/@href").extract_first()
            item['shop_title'] = li.xpath(".//div[@class='tit']/a[1]/@title").extract_first()
            item['shop_url'] = li.xpath("./div/[@class='txt']/div[@class='tit']/a[1]/@href").extract_first()
            search_ad = li.xpath("search_ad/a[@class='search-ad']")
            item['is_ad'] = False if len(search_ad) == 0 else True
            iout = li.xpath("./div/[@class='txt']/div[@class='tit']/div[1]/a[@class='iout']")
            item['is_out'] = False if len(iout) == 0 else True
            item['comment_count'] = li.xpath("./div[@class='comment']/a[1]/b")
            print(item)
