# -*- coding: utf-8 -*-
import scrapy
from fontTools.ttLib import TTFont
from io import BytesIO
from bson import ObjectId
import re
from scrapy_spiders.items import ScrapySpidersItem
import copy


class MaoyanSpider(scrapy.Spider):
    name = 'maoyan'
    allowed_domains = ['maoyan.com', 'meituan.net']

    # start_urls = ['https://maoyan.com/films?showType=3&sourceId=6&sortId=1&yearId=14']
    mongo_collection = "maoyan"
    rex_info = re.compile('.*?class="stonefont">(.*?)</span>.*?')
    rex_font = re.compile('(?<=&#x).{4}(?=;)')

    def start_requests(self):
        for i in range(3):
            yield scrapy.Request(f"https://maoyan.com/films?showType=3&sourceId=6&sortId=1&yearId={12+i}", self.parse)

    def parse(self, response):
        movie_div_list = response.xpath("//div[contains(@class,'movie-item-title')]/a/@href").extract()
        pf_div_list = response.xpath(".//div[contains(@class,'channel-detail-orange')]")
        for url, pf in zip(movie_div_list, pf_div_list):
            if not pf.xpath("./text()"):
                yield scrapy.Request(response.urljoin(url), self.parse_m)

        next_li = response.xpath("//ul[@class='list-pager']/li[last()]/a")[0]
        if next_li.xpath("./text()").extract_first() == "下一页":
            next_page = response.urljoin(next_li.xpath("./@href").extract_first())
            yield scrapy.Request(next_page, self.parse)

    def parse_m(self, response):
        item = {}
        dhhml = response.body.decode()
        # res1 = re.findall(r'(?<=<span class="stonefont">).*?(?=</span>)',dhhml)
        font_url = response.selector.re(".*?(//vfile.meituan.net/colorstone/[\w]+\.woff).*")[0]
        # item['font_id'] = response.selector.re(".*?//vfile.meituan.net/colorstone/([\w]+)\.woff.*")[0]
        item['movie_name'] = response.xpath(
            "//div[@class='movie-brief-container']/h3[@class='name']/text()").extract_first()
        item['movie_ename'] = response.xpath("//div[@class='ename ellipsis']/text()").extract_first()
        movie_info = response.xpath("//div[@class='movie-brief-container']/ul/li/text()").extract()
        item['movie_type'] = movie_info[0]
        item['movie_bron'] = movie_info[1].replace('\n', '').strip().split('/')[0].strip()
        item['movie_date'] = movie_info[2]
        # item['info_num'] = response.xpath("//span[contains(@class,'info-num')]/span/text()").extract_first()
        # item['score_num'] = response.xpath("//span[@class='score-num']/span/text()").extract_first()
        # item['piaofang'] = response.xpath("//div[@class='movie-index-content box']/span[@class='stonefont']/text()").extract_first()
        movie_info = self.rex_info.findall(dhhml)
        if len(movie_info) == 3:
            item['info_num'] = movie_info[0]
            item['score_num'] = movie_info[1]
            item['piaofang'] = movie_info[2]

            item['unit'] = response.xpath(
                "//div[@class='movie-index-content box']/span[@class='unit']/text()").extract_first()
            for k, v in item.items():
                print(k + "---" + v)
            print(font_url)
            yield scrapy.Request('http://' + font_url, self.parse_num, meta={'item': item}, dont_filter=True)

    def parse_num(self, response):
        try:
            item = copy.deepcopy(response.meta['item'])
            print(item['movie_name'])
            mapping = self.get_mapping(TTFont(BytesIO(response.body)))
            item['info_num'] = self.get_font_code(item['info_num'], mapping)
            item['score_num'] = self.get_font_code(item['score_num'], mapping)
            item['piaofang'] = self.get_font_code(item['piaofang'], mapping) + item.pop('unit')

            res = ScrapySpidersItem()
            res['collection'] = self.mongo_collection
            res['mongo_update_option'] = {
                'filter': {"_id": ObjectId()},
                "update": {"$set": item},
                "upsert": True
            }
            print(item['movie_name'])
            yield res
        except Exception as e:
            print(e)

    def get_font_code(self, text, mapping):
        re_res = self.rex_font.findall(text)
        for i in re_res:
            text = text.replace(f'&#x{i};', mapping[i])
        return text

    def get_mapping(self, test_font):
        fontdict = {'uniF6B2': '0', 'uniE668': '8', 'uniE882': '9', 'uniF527': '2', 'uniE448': '6',
                    'uniE92A': '3', 'uniF7AB': '1', 'uniE6BD': '4', 'uniF719': '5', 'uniE3E5': '7'}
        basefont = TTFont('base.woff')
        uniList = test_font['cmap'].tables[0].ttFont.getGlyphOrder()
        mapping = {}
        for i in range(1, 12):
            maoyanGlyph = test_font['glyf'][uniList[i]]
            for k, v in fontdict.items():
                baseGlyph = basefont['glyf'][k]
                if maoyanGlyph == baseGlyph:
                    mapping[uniList[i][3:].lower()] = v
        return mapping
