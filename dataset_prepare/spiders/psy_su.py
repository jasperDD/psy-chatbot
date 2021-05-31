import scrapy

#from dataset_prepare.items import DatasetPrepareItem
# https://pythonru.com/biblioteki/sozdanie-parserov-s-pomoshhju-scrapy-i-python

NEXT_PAGE_SELECTOR = '#content div:nth-child(5) a::attr(href)'
# Следующая страница в группе
def get_next_page(response):
    page_url = response.url[len('https://psy.su'):-1] # Оканчивается на знак /
    pages = response.css(NEXT_PAGE_SELECTOR).extract()
    if not pages:
        next_page = None
    elif not page_url in pages: # Первая страница
        next_page = pages[0]
    else:
        cur_index = pages.index(page_url)
        next_page = None if cur_index >= len(pages) - 1 else pages[cur_index + 1]
    return next_page

# Следующая страница в топике
def get_next_topic_page(response):
    page_url = response.url
    pages = response.css(NEXT_PAGE_SELECTOR).extract()
    if not pages:
        next_page = None
    elif '?page=' not in page_url: # Первая страница без номера
        next_page = pages[0]
    else:
        page_url_index = page_url[page_url.index('?page=') + len('?page='):]
        cur_index = int(page_url_index) - 1
        next_page = None if cur_index >= len(pages) else pages[cur_index]
    return next_page

# Получить название и идентификатор топика на странице
def get_topic_id_and_name(response):
    page_url = response.url
    topic_id = get_id_from_url(page_url, 'topic')
    topic_name = response.css('h1::text').extract_first()
    return topic_id, topic_name

# Получить идентификатор топика или профиля автора из урл
def get_id_from_url(url, type_name):
    url_el = url.split('/')
    id = url_el[url_el.index(type_name) + 1]
    return id

class PsySuSpider(scrapy.Spider):
    name = 'psy_su'
    allowed_domains = ['psy.su']
    topics_dic = {}
    start_urls = ['https://psy.su/club/forum/category/14/',  # Дети
                  'https://psy.su/club/forum/category/15/',  # Взрослые
                  'https://psy.su/club/forum/category/16/'  # Чрезвычайные ситуации
                  ]

    def parse(self, response):
        print('Procesing:', response.url)
        topics =  response.xpath('//table[@class="forum"]//tr/td/a[contains(@href, "/club/forum/topic/")]/@href').getall()

        # Следующий топик
        for topic_url in topics:
            yield scrapy.Request(
                response.urljoin(topic_url),
                callback=self.parse_topic)

        # Следующая страница группы
        next_page = get_next_page(response)
        if next_page:
            yield scrapy.Request(
                response.urljoin(next_page),
                callback=self.parse)


    def parse_topic(self, response):
        topic_id, topic_name = get_topic_id_and_name(response)

        posts = response.css('table.forum tr')
        # author_urls = posts.css('td.author a:nth-child(3)::attr(href)').extract() # Этот вариант иногда неправильное скливает тексты с авторами
        # author_names = posts.css('td.author a:nth-child(3)::text').extract()
        # texts = posts.css('td div.text p::text').extract()
        # htmls = posts.css('td div.text p').extract()
        # posts_data = zip(author_urls, author_names, texts, htmls)
        #
        # for item in posts_data:
        #     if item[2] and item[2].strip(): # TODO доработать фильтр на удаляенные сообщения, а также реализовать парсинг по цитатам и возможно фильтр исходного сообщения
        #         # TODO 2 доработать обработку HTML - смайлики и т.д.
        #         scraped_info = {
        #             'topic_id': topic_id,
        #             'topic_name': topic_name,
        #             'url': response.url,
        #             'author_id': None if item[0] is None else get_id_from_url(item[0], 'profile') ,
        #             'author_name': item[1],
        #             'text': item[2].strip(),
        #             'html': item[3]
        #         }
        #         yield scraped_info  # генерируем очищенную информацию для скрапа

        posts = posts[1:] # Первая строка заголовок
        rdy = 0
        for idx, post in enumerate(posts):
            author_url = post.css('td.author a:nth-child(3)::attr(href)').extract_first()
            author_id = None if author_url is None else get_id_from_url(author_url, 'profile')
            author_name = post.css('td.author a:nth-child(3)::text').extract_first()
            text_arr = post.xpath('./td//div[@class="text"]//text()').getall()
            text = '\n'.join(text_arr)
            html = post.xpath('./td//div[@class="text"]').get()
            if text and text.strip(): # TODO доработать фильтр на удаляенные сообщения, а также реализовать парсинг по цитатам и возможно фильтр исходного сообщения
                # TODO 2 доработать обработку HTML - смайлики и т.д.
                text = text.strip()
                scraped_info = {
                    'topic_id': topic_id,
                    'topic_name': topic_name,
                    'url': response.url,
                    'author_id': author_id,
                    'author_name': author_name,
                    'text': text,
                    'html': html
                }
                rdy += 1
                yield scraped_info # генерируем очищенную информацию для скрапа
            else:
                print('bad:', author_name, idx, f'"{text}"', html)
        print('  parsed:', response.url, rdy, 'from', len(posts))

        # Следующая страница топика
        next_topic_page = get_next_topic_page(response)
        if next_topic_page:
            yield scrapy.Request(
                response.urljoin(next_topic_page),
                callback=self.parse_topic)

