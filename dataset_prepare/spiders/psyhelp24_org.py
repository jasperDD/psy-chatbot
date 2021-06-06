import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from ..items import DatasetPrepareItem
import re
# https://psyhelp24.org/category/primer-psihologicheskoy-konsyltacii/
# Отображаются разные консультации

class Psyhelp24OrgSpider(CrawlSpider):
    name = 'psyhelp24_org'
    allowed_domains = ['psyhelp24.org']
    start_urls = ['https://psyhelp24.org/category/primer-psihologicheskoy-konsyltacii/page/1/',
                  'https://psyhelp24.org/category/primer-psihologicheskoy-konsyltacii/page/2/'
                  ]

    rules = (
        Rule(LinkExtractor(allow=r'psihologicheskaya-konsultatsiya-'), callback='parse_item'),
    )

    def parse_item(self, response):
        """ Функция парсящая диалог из страницы консльтации
        Проверка: scrapy check psyhelp24_org

        @url https://psyhelp24.org/psihologicheskaya-konsultatsiya-6/
        @returns items 1
        @scrapes author_id author_name text
        @scrapes topic_id topic_name url html
        """
        # Create
        posts = response.xpath('//div[@class="post-content"]/blockquote | //div[@class="post-content"]/p')
        topic_id = 0
        topic_name = ''
        try:
            topic_id = re.search(r'psihologicheskaya-konsultatsiya-(\d+)', response.url).group(1)
            topic_name = response.css('h2::text').extract_first()
        except:
            pass
        start_idx = 3 # Первая название темы, потом психолога, потом картинка.
        psy_name = None
        client_name = None
        if(posts[start_idx].css('blockquote').get() is not None): # Пропускаем первый тезис психолога, он об условиях до вопроса клиента
            start_idx = 4
        for idx, post in enumerate(posts[start_idx:]):
            item = DatasetPrepareItem()
            is_psy = post.css('blockquote').get() is not None
            if is_psy and psy_name is None:
                psy_name = post.xpath('.//strong/text()').get()
            elif not is_psy and client_name is None:
                client_name = post.xpath('.//strong/text()').get()
            item['author_id'] = 1 if is_psy else 0
            item['author_name'] = psy_name if is_psy else client_name
            # text_arr = post.xpath('.//text()').getall()
            text_arr = post.xpath('./text()').getall() if not is_psy else post.xpath('./p/text()').getall()
            text = '\n'.join(text_arr)
            if not text or len(text) == 1: # Для пустых и односимвольных пропускаем
                continue
            item['text'] = text.strip() if text[0] != ':' else text[1:].strip()
            item['topic_id'] = topic_id
            item['topic_name'] = topic_name
            item['url'] = response.url
            item['html'] = post.get()
            yield item
