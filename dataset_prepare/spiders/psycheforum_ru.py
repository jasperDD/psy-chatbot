from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.loader import ItemLoader

from itemloaders.processors import MapCompose, Join
from scrapy.http import Request
from ..items import DatasetPrepareItem

import re

guest_id = {}
guest_index = 0

# https://psycheforum.ru/forum/56-konsultacii-psihologov-onlayn-psihologicheskaya-pomosch/
# По психологам бесполезные достаточно диалог по одному или два ответа только

class PsycheforumRuSpider(CrawlSpider):
    name = 'psycheforum_ru'
    allowed_domains = ['psycheforum.ru']
    start_urls = [
                  'https://psycheforum.ru/forum/56-konsultacii-psihologov-onlayn-psihologicheskaya-pomosch/', # Консультации психологов онлайн, психологическая помощь
                  'https://psycheforum.ru/forum/4-forum-o-lyubvi-i-otnosheniyah-/', # Форум о любви и отношениях
                  'https://psycheforum.ru/forum/35-forum-o-sekse/', # Форум о сексе
                  'https://psycheforum.ru/forum/5-semeynye-problemy-muzh-i-zhena/', # Семейные проблемы. Муж и жена
                  'https://psycheforum.ru/forum/82-forum-o-beremennosti-i-rodah-materinstvo/', # Форум о беременности и родах, материнство
                  'https://psycheforum.ru/forum/9-detskaya-psihologiya-deti-i-roditeli/', # Детская психология, дети и родители
                  'https://psycheforum.ru/forum/25-psihologiya-lichnosti/', # Психология личности
                  'https://psycheforum.ru/forum/81-socialnaya-psihologiya-vzaimootnosheniya-s-druzyami-i-kollegami/', # Социальная психология, взаимоотношения с друзьями и коллегами
                  'https://psycheforum.ru/forum/13-psihologicheskie-konsultacii-po-drugim-voprosam/', # Психологические консультации по другим вопросам
                  'https://psycheforum.ru/forum/8-forum-psihologov-obmen-opytom-i-znaniyami/', # Форум психологов, обмен опытом и знаниями
                  'https://psycheforum.ru/forum/46-napravleniya-psihologicheskogo-konsultirovaniya/', # 	Направления психологического консультирования
                  'https://psycheforum.ru/forum/26-samousovershenstvovanie-i-psihotehnologii/', # Самоусовершенствование и Психотехнологии
                  'https://psycheforum.ru/forum/27-literatura-stati-po-psihologii-i-filosofii/', # Литература, статьи по психологии и философии
                  'https://psycheforum.ru/forum/6-psihiatriya-i-psihofarmakoterapiya/',
                  'https://psycheforum.ru/forum/37-religiya-vera/', # Религия, вера
                  'https://psycheforum.ru/forum/84-pogovorite-so-mnoy-forum-otkroveniy/', # Поговорите со мной... Форум откровений
                  'https://psycheforum.ru/forum/279-klinika-tvorchestvo-trolley/' # 	Клиника. Творчество троллей
                  ]

    # Игнорируем группы форумов ниже
    # https://psycheforum.ru/forum/298-psihologicheskie-testy/ # Психологические тесты
    # https://psycheforum.ru/forum/34-obyavleniya-psihologov/ # Объявления психологов
    # https://psycheforum.ru/forum/12-filosofskiy-forum/ # Философский форум
    # https://psycheforum.ru/forum/14-forumy-po-parapsihologii/ # Форумы по парапсихологии
    # https://psycheforum.ru/forum/85-puteshestviya-turizm-otdyh-razvlecheniya/ #  Путешествия, туризм, отдых, развлечения
    # https://psycheforum.ru/forum/2-razgovorchiki/ # Разговорчики
    # https://psycheforum.ru/forum/69-chatovka/ # ЧАТовка
    # https://psycheforum.ru/forum/23-rabota-foruma-predlozheniya-i-zamechaniya/ # Работа форума, предложения и замечания
    # https://psycheforum.ru/forum/7-arhiv-foruma/ # Архив форума
    rules = (
        # Парсим форумы, содержащие другие форумы и темы(топики)
        Rule(LinkExtractor(allow=r'/forum/', deny=r'(\.xml\/?$)|(\-#$)|(\/#ip$)|(\?do\=markRead)|(#ipsLayout)|(\/page\/\d+)|(#elSortBy)|(advancedSearchForm)|(sortby=)')),
        # Парсим следующие страницы форумов
        Rule(LinkExtractor(restrict_xpaths='//li[contains(@class,"ipsPagination_next")]')),
        # Игнорируем ссылки на топики с комментариеми в адресе, т.к. это вторые и последующие старницы со списков форумов
        # Будет неправильный порядок парсинга страниц в теме, соответственно цепочки сообщений собьются
        # Также игнорируем ссылки на правила и рекламу
        # https://psycheforum.ru/topic/154794-polzovatelskoe-soglashenie/
        # https://psycheforum.ru/topic/136149-kak-zaregistrirovatsya-na-forume-i-sozdat-temu/
        # https://psycheforum.ru/topic/154744-reputaciya-polzovateley-foruma/
        # https://psycheforum.ru/topic/154745-ignorirovanie-polzovateley/
        # https://psycheforum.ru/topic/44267-platnye-uslugi-foruma/
        # https://psycheforum.ru/topic/135209-nastroyka-uvedomleniy-s-foruma/
        # https://psycheforum.ru/topic/154791-besplatnye-konsultacii-psihologov/
        # https://psycheforum.ru/topic/154792-anonimnye-konsultacii-psihologov/
        # https://psycheforum.ru/topic/154793-platnye-konsultacii-psihologov/
        # https://psycheforum.ru/topic/44267-platnye-uslugi-foruma/
        # https://psycheforum.ru/topic/3273-reklama-na-forume-po-psihologii/
        # https://psycheforum.ru/topic/154705-o-psihologicheskom-forume/
        # https://psycheforum.ru/topic/154746-administraciya-foruma/
        # https://psycheforum.ru/topic/154795-otzyvy-i-predlozheniya/
        Rule(LinkExtractor(allow=r'/topic/', deny=r'(\/#comments)|topic\/(154794|136149|154744|154745|44267|135209|154791|154792|154793|44267|3273|154705|154746|154795)-'), callback='parse', follow=False)
    )
    # 'https://psycheforum.ru/forum/92-lyubovnyy-treugolnik/' # Раздел
    # 'li.ipsPagination_next' #Следующая страница
    #
    # 'https://psycheforum.ru/topic/97703-lyubovnaya-addikciya/?do=getNewComment' # Топик
    # 'https://psycheforum.ru/topic/97703-lyubovnaya-addikciya/page/2/#comments' #li.li.ipsPagination_next a.href rel="next"
    # #    'https://psycheforum.ru/topic/97703-lyubovnaya-addikciya/page/2/#comments' #li.

    def parse(self, response):
        """ Функция извлекающая все страницы топка для загрузки и парсящая диалог

        @url https://psycheforum.ru/topic/97703-lyubovnaya-addikciya/
        @returns items 30
        @scrapes author_id author_name text
        @scrapes topic_id topic_name url html
        """

        # Извлекаем комментарии
        posts = response.xpath('//article')

        # Извлекаем название топика и его код
        try:
            topic_regexp = re.search(r'/topic/(\d+)-', response.url) # Бывают такие https://psycheforum.ru/topic/135060-%C2%AB-ne-ori-dura-tut-vsem-bolno%C2%BB
            response.meta['topic_id'] = topic_regexp.group(1)
            response.meta['topic_name'] =  ' '.join(response.xpath('//h1//text()').extract()).strip()
        except Exception as err:
            print('Ошибка парсинга топика', err)
            return

        # Парсим все топики
        for post in posts:
            yield self.parse_post(post, response)

        # Следующая страница, ставим в конце парсинга, чтобы парсинг шел после сообщений и сохранялся их порядок по страницам
        next_topic_page = response.xpath('//li[contains(@class,"ipsPagination_next")]//@href').extract_first()
        if next_topic_page:
            yield Request(next_topic_page, callback=self.parse)

    def parse_post(self, post_selector, response):
        global guest_index
        global guest_id

        # Create the loader using the selector
        l = ItemLoader(item=DatasetPrepareItem(), selector=post_selector)
        author_name = post_selector.xpath('.//h3/strong/a/text()').extract_first()
        author_id_text = post_selector.xpath('.//h3/strong/a/@href').extract_first()
        author_id_regexp = None if author_id_text is None else re.search(r'/profile/(\d+)-', author_id_text)
        if author_id_regexp is not None:
            author_id = author_id_regexp.group(1)
        else:
            author_id = guest_id.get(author_name)
            if author_id is None:
                author_id = f'gst_{guest_index}'
                guest_id[author_name] = author_id
                guest_index += 1
        l.add_value('author_id', author_id)
        l.add_value('author_name', author_name)
        l.add_xpath('text', './/div[@data-role="commentContent"]//text()',
                     MapCompose(str.strip), Join('\n'))
        l.add_value('topic_id',  response.meta['topic_id'])
        l.add_value('topic_name',  response.meta['topic_name'])
        l.add_value('url',  response.url)
        l.add_xpath('html', './/div[@data-role="commentContent"]',
                    MapCompose(str.strip), Join('\n'))
        return l.load_item()

# scrapy crawl psycheforum_ru -s JOBDIR=crawls/psycheforum_ru-9 -L INFO
# 2021-06-07 14:39:58 [scrapy.core.engine] INFO: Spider opened
# 2021-06-07 16:13:07 [scrapy.extensions.feedexport] INFO: Stored csv feed (31869 items) in: ./data/data_psycheforum_ru.csv
# 2021-06-07 16:24:52 [scrapy.core.scheduler] INFO: Resuming crawl (789 requests scheduled)
#1:45
#2021-06-07 16:24:52 [scrapy.core.engine] INFO: Spider opened
#2021-06-07 18:39:53 [scrapy.extensions.feedexport] INFO: Stored csv feed (58495 items) in: ./data/data_psycheforum_ru.csv
# 2:15

#2021-06-07 21:43:34 [scrapy.core.scheduler] INFO: Resuming crawl (902 requests scheduled)
#2021-06-08 08:35:00 [scrapy.extensions.feedexport] INFO: Stored csv feed (229790 items) in: ./data/data_psycheforum_ru.csv

#2021-06-08 12:26:14 [scrapy.extensions.logstats] INFO: Crawled 2986 pages (at 14 pages/min), scraped 66672 items (at 262 it

# 2021-06-09 08:30:04 [scrapy.extensions.logstats] INFO: Crawled 19687 pages (at 13 pages/min), scraped 458447 items (at 170 items/min)
# 2021-06-09 08:30:08 [scrapy.extensions.feedexport] INFO: Stored csv feed (458469 items) in: ./data/data_psycheforum_ru.csv
