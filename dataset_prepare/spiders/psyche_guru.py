import scrapy
import pyppeteer

from dataset_prepare.items import DatasetPrepareItem
# https://pypi.org/project/scrapy-pyppeteer/
# https://github.com/elacuesta/scrapy-pyppeteer

class PsycheGuruSpider(scrapy.Spider):
    name = 'psyche_guru'
    allowed_domains = ['forum.psyche.guru']
    start_urls = ['https://forum.psyche.guru/']

    def parse(self, response):
        print("procesing:" + response.url)
        # Извлечение данных с помощью селекторов CSS
        product_name = response.css('.item-title::text').extract()
        pass
