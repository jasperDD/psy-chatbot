#%%
import os
import pandas as pd
from bs4 import BeautifulSoup
from scrapy.selector import Selector

#%% # psy_ru

html1 = """
<div class="text">
  <div class="forum_quote">
    <div class="name">Захарова Людмила:</div>
    <div class="quote">И главное. 
      Как Вы работаете с "выгоревшими", каким образом можно мотивировать человека на смену стереотипа деятельности, "активировать"? 
      Где ему, бедняге, взять силы, а главное возможности (в том числе и материальные), чтобы заняться любимым делом да ещё и добиться
      соответствующего денежного вознаграждения (с учётом объективной реальности)?
    </div>
  </div>
  <b>###Присоединяюсь к вопросу. И, пожалуйста, по содержанию. Коль уж Вы так любите самоутверждаться - нет проблем, но и содержание<b>
  добавляйте  :lol: . Первое мы как-нибудь переживем, а вторым воспользуемся. Или Вы из тех специалистов, для которых коллеги - 
  конкуренты, и поэтому рот на замок, а слово "польза" вызывает у Вас мучительные переживания? 
  <div class="forum_quote">
    <div class="quote">
      Читатели, читайте внимательно собственые высказывания типа "Но интересна не книжная теория, а просто опишите Ваши ощущения...".  
      Вы когда перескакиваете на другое, так хоть как-то мотивируйте. Так что у Вас-то, Евгений? Вы просто пришли на форум рассказать о
      себе? Или ищете коллег по специфике деятельности и просто неправильно запрос сформулировали, что Вам про собственные ощущения 
      стали рассказывать?  :smile:
    </div>
  </div>
  <em>####text 2</em>
</div>
"""
topic_dialog = []
post_sel = Selector(text=html1)
quotes_all = post_sel.xpath('//div[@class="text"]/div[@class="forum_quote"]/div[@class="quote"]/div[@class!="forum_quote"]//text()').getall()
# quot1 = post_sel.xpath('//div[@class="text"]/div[@class="forum_quote"]')[0].get()
text_all = post_sel.xpath('//div[@class="text"]//div[not(@class="forum_quote")]//text()').getall()
print(len(quotes_all), len(text_all))
if text_all and quotes_all:
    if len(text_all) > len(quotes_all):
        text_all = text_all if text_all[0].strip() else text_all[1:] # Первый текст до цитат пропускаем
    for quote, text in zip(quotes_all, text_all): # Лишнюю дилну откидываем
        # print(quote.strip())
        # print(text.strip())
        topic_dialog.append((quote.strip(), text.strip()))
        # print('-----')
print(topic_dialog)
# print('\n!'.join(text_all))
# print('\n!'.join(text_all))

#%% # b17
html2 = """
<td class="mes qq" fio="№2 | u48976 | Шиян Ольга Васильевна">
  <div class="quote">
    <b>№0 | Страстный гештальт писал(а):</b><br>
    <div class="quote">
        <b>№0 | ктот писал(а):</b>
        ЦИТАТА 0
    </div>
    <b>ЦИТАТА 1</b>
  </div>
  ТЕКСТ 1
  <div class="quote">
    <b>№1 | Sostenuto писал(а):</b>
    <br>ЦИТАТА 2<br>
    ЦИТАТ 2а
  </div>
  ТЕКСТ 2<br>
  ТЕКСТ 2а
</td>
"""
html2 = """
<td class="mes qq" fio="№1 | u714134 | Sostenuto">
  <div class="quote">
    <b>№0 | Страстный гештальт писал(а):</b>
    <br>
  </div>
  Это нормально. Если я не спешу, могу познакомиться и поговорить. Если спешу - так и скажу. И пойду по делам 
  <br>
  Сама именно на улице не знакомилась. Обычно знакомилась в зданиях)))
</td>
"""

topic_dialog = []
post_sel = Selector(text=html2)
quotes_all = post_sel.xpath('//td[@class="mes qq"]/div[@class="quote"]') # TODO вложенную цитаты вытаскивает как текст
text_all = post_sel.xpath('//td[@class="mes qq"]//text()').getall()
text_all = [x.strip() for x in text_all if x.strip()]
print(quotes_all)
print(text_all)

for idx, quote in enumerate(quotes_all):
    quote_arr = quote.xpath('.//text()').getall()
    quote_arr = [x.strip() for x in quote_arr if 'писал(а)' not in x and x.strip()] # Удаляем загловки цитаты
    if not quote_arr:
        continue
    quote_res = '\n'.join(quote_arr)
    print('@', quote_arr)
    print(quote_res)
    text_start_idx = text_all.index(quote_arr[len(quote_arr) - 1]) + 1 # TODO возможно не уникальный текст в цитате или вообще пустая, лучше проверять все значения цитаты
    text_end_idx = len(text_all)
    for i, el in enumerate(text_all[text_start_idx:]):
        if 'писал(а)' in el:
            text_end_idx = text_start_idx + i
            break
    text_res = '\n'.join(text_all[text_start_idx: text_end_idx])
    # print(quote_res)
    # print(text_start_idx, text_end_idx, text_all[text_start_idx: text_end_idx])
    topic_dialog.append((quote_res, text_res))
print(len(topic_dialog), topic_dialog)

#%% # psyforum.ru
html3 = """
<div data-role="commentContent" class="ipsType_normal ipsType_richText ipsPadding_bottom ipsContained" data-controller="core.front.core.lightboxedImages">
  <blockquote data-ipsquote="" class="ipsQuote" data-ipsquote-contentcommentid="5717987" data-ipsquote-contentapp="forums" data-ipsquote-contenttype="forums" data-ipsquote-contentclass="forums_Topic" data-ipsquote-contentid="130830" data-ipsquote-username="Alakey" data-cite="Alakey" data-ipsquote-timestamp="1512479037">
    <div>
      <div>
        <p>Если мужчина в 21 год до сих пор девственник то он на всю жизнь останется девственников? </p>
      </div>
    </div>
  </blockquote>
  <p>Это в каком законе написано?)</p>
  <blockquote data-ipsquote=" class="ipsQuote" data-ipsquote-contentcommentid="5717987" data-ipsquote-contentapp="forums" data-ipsquote-contenttype="forums" data-ipsquote-contentclass="forums_Topic" data-ipsquote-contentid="130830" data-ipsquote-username="Alakey" data-cite="Alakey" data-ipsquote-timestamp="1512479037">
    <div>
      <div>
        <p>Виноват ли поздний девственник в своей девственности или это вина женщин, которые не выбрали его не захотели с ним заниматься сексом? </p>
      </div>
    </div>
  </blockquote>
  <p>В 21 год - это ещё не поздний девственник. И слово "вина" здесь не подходит. Просто не сложилось.</p>
  <blockquote data-ipsquote="" class="ipsQuote" data-ipsquote-contentcommentid="5717987" data-ipsquote-contentapp="forums" data-ipsquote-contenttype="forums" data-ipsquote-contentclass="forums_Topic" data-ipsquote-contentid="130830" data-ipsquote-username="Alakey" data-cite="Alakey" data-ipsquote-timestamp="1512479037">
    <div>
      <div>
        <p>Как вообще помочь поздним девственникам если женщины их просто не воспринимают как сексуальных  партнеров? </p>
      </div>
    </div>
  </blockquote>
  <p>Найти ту, которая воспримет.</p>
  <span class="ipsType_reset ipsType_medium ipsType_light" data-excludequote>
    <strong>Изменено 
       <time datetime="2017-12-05T13:07:55Z" title="05.12.2017 13:07 " data-short="3 г">5 декабря 2017</time>
        пользователем Кнехт
    </strong>
  </span>
</div>
"""
post_sel = Selector(text=html3)
quotes_all = post_sel.xpath('//div[@data-role="commentContent"]/blockquote') # TODO вложенную цитаты вытаскивает как текст
text_all = post_sel.xpath('//div[@data-role="commentContent"]//p//text()').getall()
text_all = [x.strip() for x in text_all if x.strip()]
print(quotes_all)
print(text_all)
topic_dialog = []

for idx, quote in enumerate(quotes_all):
    quote_arr = quote.xpath('.//p//text()').getall()
    quote_arr = [x.strip() for x in quote_arr if x.strip()] # Удаляем пустые тексты
    if not quote_arr:
        continue
    quote_res = '\n'.join(quote_arr)
    text_start_idx = None
    for txt_idx, text in enumerate(text_all): # Ищем индекс в тексте окончания цитаты
        if quote_arr[len(quote_arr) - 1] in text: # TODO возможно не уникальный текст в цитате или вообще пустая, лучше проверять все значения цитаты
            text_start_idx = txt_idx + 1 if txt_idx + 1 < len(text_all) else None # Если после цитаты еще есть текст, если нет то это нет ответа
            break
    if text_start_idx is None: # Если в текстах не нашли последнюю фразу цитаты, пропускаем
        continue
    text_end_idx = len(text_all)
    next_quote = quotes_all[idx + 1] if idx + 1 < len(quotes_all) else None
    if next_quote is not None:
        next_quote_arr = next_quote.xpath('.//p//text()').getall()
        next_quote_arr = [x.strip() for x in next_quote_arr if x.strip()] # Удаляем пустые тексты
        if next_quote_arr: # Если следующая цитата не пустая # TODO пустая, но например за ней текст? Или еще цитата?
            next_quote_val = next_quote_arr[0]
            for i, el in enumerate(text_all[text_start_idx:]):
                if next_quote_val == el:
                     text_end_idx = text_start_idx + i
                     break
    text_res = '\n'.join(text_all[text_start_idx: text_end_idx])
    topic_dialog.append((quote_res, text_res))
print(len(topic_dialog), topic_dialog)
