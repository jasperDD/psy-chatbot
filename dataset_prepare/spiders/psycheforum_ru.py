import scrapy

# https://psycheforum.ru/forum/56-konsultacii-psihologov-onlayn-psihologicheskaya-pomosch/
# По психологам бесполезные достаточно диалог по одному или два ответа только

# https://psycheforum.ru/
# Здесь горазд больше ответов
# Много используется цитат, возможно эффективней только на них обращать внимание и разбивать вопросы ответы по ним

# Парсится scrapy

class PsycheforumRuSpider(scrapy.Spider):
    name = 'psycheforum_ru'
    allowed_domains = ['psycheforum.ru']
    start_urls = ['http://psycheforum.ru/']

    def parse(self, response):
        pass
