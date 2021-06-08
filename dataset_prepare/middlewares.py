# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from scrapy.exceptions import IgnoreRequest
import random

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter


class DatasetPrepareSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.
        print('process_spider_input', response.url, response.status)
        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.
        print('process_spider_output', response.url, response.status)
        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.
        print('process_spider_exception', response.url, response.status)
        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class DatasetPrepareDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.
    def __init__(self, crawler):
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls(crawler)
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        if response.status == 503  and 'b17.ru' in response.url:
            # Доступ к сайту b17.ru для вашего IP адреса временно заблокирован.
            # Ваш IP: 212.19.7.98
            # Доступ к сайту b17.ru для вашего IP адреса временно заблокирован.<br>Ваш IP: 212.19.7.98<br><br>Если Вы не бот, то для разблокировки <a href='/ip_unban.php' rel="nofollow">перейдите по ссылке</a>.
            if 'Доступ к сайту b17.ru для вашего IP адреса временно заблокирован' in response.text:
                print(f'[!!! ERROR] Ошибка {response.status}. b17.ru внес IP в бан, нужно вмешательство. Останавливаем скрапер. Текст:\n', response.text)
                self.crawler.stop()
            # Возвращаем response, чтобы его внесло в списко повторных запросов.
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)

# Использование случайного прокси с определенной вероятностью
PROXIES = [] # ['https://user:pass@proxy.com']
class CustomHttpProxyMiddleware:
    def process_request(self, request, spider):
        if self.use_proxy(request):
            p = random.choice(PROXIES)
            try:
                request.meta['proxy'] = p #"http://%s" % p['ip_port']
            except Exception as e:
                print(f'Exception {e}')

    def use_proxy(self, request):
        """
        Используем прямую загрузку для depth <= 2
        Реализуем вероятность использовать прокси 0.5
        """
        if not PROXIES: # Если нет прокси в списке, не используем
            return False
        if 'depth' in request.meta and int(request.meta['depth']) <= 2:
            return False
        i = random.randint(1, 10)
        return i <= 4

# Поизвольная замена названия браузера
AGENTS = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 YaBrowser/21.5.1.330 Yowser/2.5 Safari/537.36']
class CustomUserAgentMiddleware(object):
    def process_request(self, request, spider):
        agent = random.choice(AGENTS)
        request.headers['User-Agent'] = agent
