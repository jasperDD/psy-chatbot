from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.loader import ItemLoader

from scrapy.spidermiddlewares.httperror import HttpError
# from twisted.internet.error import DNSLookupError
# from twisted.internet.error import TimeoutError, TCPTimedOutError

from itemloaders.processors import MapCompose, Join, TakeFirst
from scrapy.http import Request
from ..items import DatasetPrepareItem
import re

class B17RuSpider(CrawlSpider):
    name = 'b17_ru'
    allowed_domains = ['b17.ru']
    start_urls = ['https://www.b17.ru/forum/',
                  'https://www.b17.ru/forum/?mod=discussion',
                  ]
    # https://www.b17.ru/forum/?mod=discussion&page_full=1#page-list
    rules = (
        # Игнорируем ссылки на последние сообщения в топиках, чтобы не сбился порядок
        Rule(LinkExtractor(allow=r'\/forum\/topic\.php\?id=', deny=r'&p='), callback='parse', follow=False),
        # Парсим следующие страницы списка топиков
        Rule(LinkExtractor(restrict_xpaths='////span[@class="page_next"][2]'))
        # Кроме топиков и явно указанных следующих страниц игнорируем все остальные ссылки
    )

    def parse(self, response):
        """ Функция извлекающая все страницы топика для загрузки и парсящая диалог

        @url https://www.b17.ru/forum/topic.php?id=365771
        @returns items 50
        @returns requests 1
        @scrapes author_id author_name text
        @scrapes topic_id topic_name url html
        """

        # Извлекаем название топика и его код
        try:
            topic_regexp = re.search(r'\/topic\.php\?id=(\d+)', response.url)
            response.meta['topic_id'] = topic_regexp.group(1)
            response.meta['topic_name'] = Join('-')(MapCompose(str.strip, lambda x: x if x else None)(response.xpath('//h1//text()').extract()))
            assert response.meta['topic_name'] and response.meta['topic_id']
        except Exception as err:
            print('Ошибка парсинга топика', err)
            return

        # Извлекаем посты топика
        if response.meta.get('is_next_page'):  # Первый пост топика повторяется на каждой странице
            posts = response.xpath('//div[@id="topic_post_list"]/div/table/tr[1]')
        else:  # Первый пост включаем в топики только на первой странице
            posts = response.xpath(
                '//div[@id="table-forum-post"]/div[1]/table/tr[1] | //div[@id="topic_post_list"]/div/table/tr[1]')
        # Парсим все топики
        for post in posts:
            yield self.parse_post(post, response)

        # Следующая страница, ставим в конце парсинга, чтобы парсинг шел после сообщений и сохранялся их порядок по страницам
        next_topic_page = response.xpath(
            '//div[@class="body_padding"]/div[@class="page-list"]/span/a[@rel="nofollow"]/@href').extract_first()
        if next_topic_page:
            yield Request(response.urljoin(next_topic_page), meta={"is_next_page": True}, callback=self.parse)

    def parse_post(self, post_selector, response):
        l = ItemLoader(item=DatasetPrepareItem(), selector=post_selector)
        l.add_xpath('author_id', './td[1]/p[@class="fio"]//@href', TakeFirst(), MapCompose(str.strip, lambda x: re.search(r'\/(.+)\/', x).group(1)))
        l.add_xpath('author_name', './td[1]/p[@class="fio"]//text()', TakeFirst(), MapCompose(str.strip))
        l.add_value('topic_id', response.meta['topic_id'])
        l.add_value('topic_name', response.meta['topic_name'])
        l.add_value('url', response.url)
        l.add_xpath('text', './td[2]//text()', MapCompose(str.strip), Join('\n'))
        l.add_xpath('html', './td[2]', MapCompose(str.strip), Join('\n'))
        return l.load_item()

#scrapy crawl b17_ru -s JOBDIR=crawls/b17_ru-1.old -L DEBUG
#scrapy crawl b17_ru -s JOBDIR=crawls/b17_ru-1
# 2021-06-07 14:59:42 [scrapy.core.engine] INFO: Spider opened
# 2021-06-07 18:39:56 [scrapy.extensions.feedexport] INFO: Stored csv feed (164052 items) in: ./data/data_b17_ru.csv
# 021-06-08 18:35:48 [scrapy.extensions.logstats] INFO: Crawled 6973 pages (at 13 pages/min), scraped 274673 items
