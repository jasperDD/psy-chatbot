# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class DatasetPrepareItem(scrapy.Item):
    # define the fields for your item here like:
    author_id = scrapy.Field()
    author_name = scrapy.Field()
    text = scrapy.Field()
    topic_id = scrapy.Field()
    topic_name = scrapy.Field()
    url = scrapy.Field()
    html = scrapy.Field()

class DialogChain(scrapy.Item):
    speaker0_text = scrapy.Field()
    speaker1_text = scrapy.Field()
