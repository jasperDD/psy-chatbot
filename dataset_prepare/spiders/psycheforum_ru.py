from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.loader import ItemLoader
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
                  # 'https://psycheforum.ru/forum/56-konsultacii-psihologov-onlayn-psihologicheskaya-pomosch/', # Консультации психологов онлайн, психологическая помощь
                  'https://psycheforum.ru/forum/4-forum-o-lyubvi-i-otnosheniyah-/', # Форум о любви и отношениях
                  # 'https://psycheforum.ru/forum/35-forum-o-sekse/', # Форум о сексе
                  # 'https://psycheforum.ru/forum/5-semeynye-problemy-muzh-i-zhena/', # Семейные проблемы. Муж и жена
                  # 'https://psycheforum.ru/forum/82-forum-o-beremennosti-i-rodah-materinstvo/', # Форум о беременности и родах, материнство
                  # 'https://psycheforum.ru/forum/9-detskaya-psihologiya-deti-i-roditeli/', # Детская психология, дети и родители
                  # 'https://psycheforum.ru/forum/25-psihologiya-lichnosti/', # Психология личности
                  # 'https://psycheforum.ru/forum/81-socialnaya-psihologiya-vzaimootnosheniya-s-druzyami-i-kollegami/', # Социальная психология, взаимоотношения с друзьями и коллегами
                  # 'https://psycheforum.ru/forum/13-psihologicheskie-konsultacii-po-drugim-voprosam/', # Психологические консультации по другим вопросам
                  # https://psycheforum.ru/forum/8-forum-psihologov-obmen-opytom-i-znaniyami/, # Форум психологов, обмен опытом и знаниями
                  # 'https://psycheforum.ru/forum/46-napravleniya-psihologicheskogo-konsultirovaniya/', # 	Направления психологического консультирования
                  # 'https://psycheforum.ru/forum/26-samousovershenstvovanie-i-psihotehnologii/', # Самоусовершенствование и Психотехнологии
                  # 'https://psycheforum.ru/forum/27-literatura-stati-po-psihologii-i-filosofii/', # Литература, статьи по психологии и философии
                  # 'https://psycheforum.ru/forum/6-psihiatriya-i-psihofarmakoterapiya/',
                  # 'https://psycheforum.ru/forum/37-religiya-vera/', # Религия, вера
                  # 'https://psycheforum.ru/forum/84-pogovorite-so-mnoy-forum-otkroveniy/', # Поговорите со мной... Форум откровений
                  # https://psycheforum.ru/forum/279-klinika-tvorchestvo-trolley/ # 	Клиника. Творчество троллей
                  ]

    # Игнорируем ниже в rules
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
        Rule(LinkExtractor(allow=r'/forum/')),
        # Парсим следующие страницы форумов
        Rule(LinkExtractor(restrict_xpaths='//li[contains(@class,"ipsPagination_next")]')),
        # Игнорируем ссылки на топики с комментариеми в адресе, т.к. это вторые и последующие старницы со списков форумов
        # Будет неправильный порядок парсинга страниц в теме, соответственно цепочки сообщений собьются
        Rule(LinkExtractor(allow=r'/topic/', deny=r'/#comments'), callback='parse_topic', follow=False)
    )
    # 'https://psycheforum.ru/forum/92-lyubovnyy-treugolnik/' # Раздел
    # 'li.ipsPagination_next' #Следующая страница
    #
    # 'https://psycheforum.ru/topic/97703-lyubovnaya-addikciya/?do=getNewComment' # Топик
    # 'https://psycheforum.ru/topic/97703-lyubovnaya-addikciya/page/2/#comments' #li.li.ipsPagination_next a.href rel="next"
    # #    'https://psycheforum.ru/topic/97703-lyubovnaya-addikciya/page/2/#comments' #li.

    def parse_topic(self, response):
        """ Функция извлекающая все страницы топка для загрузки и парсящая диалог

            @url https://psycheforum.ru/topic/97703-lyubovnaya-addikciya/
            @returns items 1
            @scrapes author_id author_name text
            @scrapes topic_id topic_name url html
            """
        global guest_index
        global guest_id
        # Следующая страница
        next_selectors = response.xpath('//li[contains(@class,"ipsPagination_next")]//@href')
        for url in next_selectors.extract():
            yield Request(url)

        # Извлекаем комментарии
        posts = response.xpath('//article')
        if len(posts) <= 2: # Короткие топики пропускаем, обычно в них пустой вопрос и пустой ответ или уточняющий вопрос
            pass
        topic_id = 0
        topic_name = ''
        try:
            topic_id = re.search(r'/topic/(\d+)-\w+/', response.url).group(1)
            topic_name = response.css('h1::text').extract_first()
        except:
            pass
        pass
        for idx, post in enumerate(posts):
            item = DatasetPrepareItem()
            item['author_name'] = post.xpath('//h3/strong/a/text()').extract()
            author_id_regexp = re.search(r'/profile/(\d+)-\w+/', post.xpath('//h3/strong/a/@href').extract_first())
            if author_id_regexp is not None:
                author_id = author_id_regexp.group(1)
            else:
                author_id = guest_id.get(item['author_name'])
                if author_id is None:
                    author_id = f'gst_{guest_index}'
                    guest_id[item['author_name']] = author_id
                    guest_index += 1
            item['author_id'] = author_id
            text = post.xpath('//div[@data-role="commentContent"]//text()').extract_first().strip()
            if not text or len(text) == 1: # Для пустых и односимвольных пропускаем
                continue
            item['text'] = text
            item['topic_id'] = topic_id
            item['topic_name'] = topic_name
            item['url'] = response.url
            item['html'] = post.xpath('//div[@data-role="commentContent"]').extract()
            print(item)
            yield item


