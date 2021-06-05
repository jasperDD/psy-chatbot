import scrapy
import pyppeteer

from dataset_prepare.items import DatasetPrepareItem
# https://pypi.org/project/scrapy-pyppeteer/
# https://github.com/elacuesta/scrapy-pyppeteer

class PsycheGuruSpider(scrapy.Spider):
    name = 'psyche_guru'
    allowed_domains = ['forum.psyche.guru']
    # start_urls = ['https://forum.psyche.guru/']

    # Using a dummy website to start scrapy request
    def start_requests(self):
        url = "https://psy.su/club/forum/"
        yield scrapy.Request(url=url, callback=self.parse_psychologist)

    def parse(self, response):
        print("procesing:" + response.url)
        # Извлечение данных с помощью селекторов CSS
        product_name = response.css('.item-title::text').extract()
        pass

    def parse_psychologist(self, response):
        # driver = webdriver.Chrome()  # To open a new browser window and navigate it

        # Use headless option to not open a new browser window
        options = webdriver.ChromeOptions()
        options.add_argument("headless")
        desired_capabilities = options.to_capabilities()
        driver = webdriver.Chrome(desired_capabilities=desired_capabilities)
