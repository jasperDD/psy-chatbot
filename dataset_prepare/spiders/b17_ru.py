import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.http import Request

class B17RuSpider(CrawlSpider):
    name = 'b17_ru'
    allowed_domains = ['b17.ru']
    start_urls = ['https://www.b17.ru/forum/',
                  # 'https://www.b17.ru/forum/?mod=discussion',
                  ]

    rules = (
        # Парсим следующие страницы списка топиков
        Rule(LinkExtractor(restrict_xpaths='////span[@class="page_next"][2]')),
        # Игнорируем ссылки на последние сообщения в топиках, чтобы не спиблся порядок
        Rule(LinkExtractor(allow=r'/forum/topic.php?id=', deny=r'&p='), callback='parse_topic', follow=False)
    )

    def parse_topic(self, response):
        """ Функция извлекающая все страницы топка для загрузки и парсящая диалог

        @url https://www.b17.ru/forum/topic.php?id=365771
        @returns items 1
        @scrapes author_id author_name text
        @scrapes topic_id topic_name url html
        """

        # Следующая страница
        next_topic_page = response.xpath('//div[@class="body_padding"]/div[@class="page-list"]/span/a[@rel="nofollow"]/@href').extract_first()
        print('Следующая страница', next_topic_page, response.urljoin(next_topic_page))
        if next_topic_page:
            yield Request(next_topic_page, callback=self.parse_topic)

