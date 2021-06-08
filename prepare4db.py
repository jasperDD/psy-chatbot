#%%
import os
import pandas as pd
from bs4 import BeautifulSoup
from scrapy.selector import Selector
import pprint
import re
from transformers import AutoTokenizer # AutoModelForCausalLM,

# TODO идеи цепочек
# первая автор, потом все остальные ответ, если не явные цитаты до сообщения автора.
# Т.е. повторяем логику да-но.
# Если цитата - то разбираем только цитаты, пару сообщению не делаем, если нет других сообщений без цитаты.

# TODO определения инициатора - по оценки наличие вопросов в сообщении. Если сообщение начинается с вопроса или в нем их несколько.
# То вероятно это сообщение от другого пользователя - вопрос к другим учатсникам, если участников несколько.
# Если участников два - то это уточняющие вопросы. Но в целом это лоигка не всегда возможна
# Возможно ещё оценивать по сентименту - вопрошающий о проблеме, вероятно будет сентимент груснтый использовать

# TODO
# Исключения возможны. Альтернатива - цепочка 1-2, 2-3, 3-4 в ней даже ответы других участников потенциально относятся к теме.

# TODO Короткие топики пропускаем на 1 сообщение точно, на 2 - обычно в них пустой вопрос или пустой ответ или уточняющий вопрос


#%%
MODEL_PATH='./model'
MODEL_CACHE='./model-cache'
TCV_FILE='./data/dataset.tsv'

if not os.path.exists(MODEL_PATH):
    MODEL_NAME = 'sberbank-ai/rugpt3small_based_on_gpt2'
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, cache_dir=MODEL_CACHE)
else:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)

#%%
# Таблица замены символов в диалогах
character_map = {
    ord(' '): ' ',
    ord('\n'): ' ',
    ord('\t'): ' ',
    ord('\r'): None
}
#%%
#######################################
# Вариант цеопчек 1:  1 и 2 спекер только.
def dialog_chain_variant1(topic_data):
    speaker0, speaker1 = get_pair_of_speaker(topic_data)
    if speaker1 is None:
        return None
    print(speaker0, speaker1, len(topic_data))
    topic_dialog = get_dialog_chain(topic_data, speaker0, speaker1)
    return topic_dialog

def get_pair_of_speaker(topic):
    """ Определенияе пары спискеров в диалогах

    :param topic:
    :return:
    """
    speaker0 = topic['author_id'].iloc[0]
    speaker1 = None
    for author_id in topic['author_id']:
        if author_id != speaker0:
            speaker1 = author_id
            break
    return speaker0, speaker1

def get_dialog_chain(topic, speaker0: str, speaker1: str) -> list:
    """Функция построения диалоговых пар в форумах.
    Реализуемая логика:
        - определяется автор первого сообщения,т.е топика, все его сообщения до следующего автора объединяются в одно
        - при нахождени вследующего автора, он фиксируется и собираются все его сообщения до следующего сообщения автора топика
        - цикал повторяется, все другие авторы топика игнорируются, цитаты не учтиываются. требуется доработка
    НЕДОСТАТКИ:  не выстраивает логику ответов в обсужданиях, считает что ответ идет на предыдущий пост, а не например
    на последующие посты. Не учитывает, что на часть постов отвечал другой и что второй автор может отвечать на посты
    других авторов. Нужно реализовать другую логику.

    :param topic: - список всех соощений топика впорядке постов
    :param speaker0: - идентификатор спикера 0
    :param speaker1: - идентификатор спискера 1
    :return: возвращает массив пар вопрос спискера 1 и ответа спикера 2
    """
    cur_speaker = speaker0
    cur_sentence = ''
    cur_chain_cell = []
    dialog = []
    topic_filtered = topic[topic['author_id'].isin([speaker0, speaker1])]
    # topic_filtered = topic_filtered.drop_duplicates(subset='text') # TODO надо править в парсере, чтобы не парсил несколько раз одну страницу - парсер нормальный, дописывал файл при нескольких запусках.
    # print('chain\n')
    # pprint.pprint(topic_filtered)


    for idx, post in topic_filtered.iterrows():
        # text = re.sub("^[\s\n\r]+|\n|\r|[\s\n\r]+$", ' ', post['text'])
        text = post['text'].translate(character_map)
        if post['author_id'] == cur_speaker: # Продолжаются посты этого автора
            cur_sentence += text if not cur_sentence else f' {text}' # TODO проверять и  добавлять точку в конца предыдущего сообщения?
            # print('############Автор тот же', idx, cur_speaker)
        else: # Автор сменился
            cur_chain_cell.append(cur_sentence)
            if cur_speaker is speaker1:
                dialog.append(cur_chain_cell)
                cur_chain_cell = []
                # print('############НОВАЯ ЦЕПОЧКА', idx)
            cur_speaker = post['author_id']
            cur_sentence = text
            # print('############Автор сменился. Новая строка', idx, cur_speaker)
    if cur_speaker == speaker1 and len(cur_chain_cell) and cur_sentence: # Если уже второй автор и есть текст, сохраняем последние значения
        # print('############ДОБАВИЛИ ПОСЛЕДНЮЮ ЦЕПОЧКУ', idx)
        cur_chain_cell.append(cur_sentence)
        dialog.append(cur_chain_cell)
    return dialog
# окончание варианта 1
########################

#%%
def get_length_param(text: str) -> str:
    """Функция определения длины для спикера, такая же используется в самом диалоге

    :param text: входной текст
    :return: - возвращает строку, кодирующую длину в общуающем датасете
    """
    tokens_count = len(tokenizer.encode(text))
    if tokens_count <= 15:
        len_param = '1'
    elif tokens_count <= 50:
        len_param = '2'
    elif tokens_count <= 256:
        len_param = '3'
    else:
        len_param = '-'
    return len_param

#%%
def prepare_to_dialog_format(dialog: list) -> list:
    """Функция формирования строки обучающего датасета

    :param dialog: список диалоговых пар
    :return: возвращает предподготовленный датасет
    """
    topic_dataset = []
    for row in dialog:
        spk0_len = get_length_param(row[0])
        spk1_len = get_length_param(row[1])
        dialog_str = f'|0|{spk0_len}|{row[0]}|1|{spk1_len}|{row[1]}'
    # for spk0, spk1 in dialog:
    #     spk0_len = get_length_param(spk0)
    #     spk1_len = get_length_param(spk1)
    #     dialog_str = f'|0|{spk0_len}|{spk0}|1|{spk1_len}|{spk1}'
        topic_dataset.append(dialog_str)
    return topic_dataset
#%%
DATA_PATH='./data'

dataset_files = []
for file in os.listdir(DATA_PATH):
    if file.endswith('.csv'):
        dataset_files.append(os.path.join(DATA_PATH, file))

print('Список файлов датасетов', dataset_files)

#%%
##############################
# ВАРИАНТ 2 создания цепочек диалогов
# TODO В зависимости от адреса источника, определяем стиль CSS цитат и разбиваем все цитаты в сообщении на пары вопрос-ответ
def get_quotes(post):
    post_sel = Selector(text=post['html'])
    # soup = BeautifulSoup(post['html'], 'html.parser')
    if 'psy.su' in post['url']:
        quotes = post_sel.xpath('//div[@class="text"]/div[@class="forum_quote"]')
        if(len(quotes) > 1):
            print(len(quotes), post['url'], '\n', quotes[0].get(),'\n', quotes[1].get())
        return None
        quotes = soup.select('div.text > div.forum_quote') # soup.find_all("div", class_="forum_quote")
        if quotes:
            quote_el = quotes[0].find('div', class_='quote')
            quote = quote_el.find(text=True, recursive=False) if quote_el else ''
            text_el = soup.select('div.text')
            text = text_el[0].find(text=True, recursive=False) if text_el else ''
            if quote and text:
                # print(post['url'], len(quotes),  quotes[0], '\n', soup.prettify())
                # print('###q>', quote, '\nt>', text)
                return [quote, text]
    return None

#%%
def dialog_chain_variant2(topic_data):
    topic_starter_id  = topic_data['author_id'].iloc[0]
    if topic_starter_id is None:
        return None
    topic_dialog = []
    dialog_part = {topic_starter_id: ''}
    print(dialog_part)
    for idx, post in topic_data.iterrows():
        quotes = get_quotes(post)
        if quotes is not None: # Если сообщение содержит цитирование, тогда добавляем все пары цитата и ответ как отдельные цепочки, в цеопчки сообщений не учитываем
             topic_dialog.extend(quotes)
             continue

        # TODO реализуем лоигку построения цепочек первое сообщение в серии цепочки автора топика, последующие ответы
        #   на него, до сообщения автора топика.

        # TODO подумать, если ответов автора давно не было, т.е. дискусия носит общий характер и все отвечают друг-другу.
        #   Возможно тогда логика должна учтиывать ответы других авторов и перезапускать цепочки уже от них. Выявлять
        #   чередования и т.д. - более сложная логика.


    # print(speaker0, speaker1, len(topic_data))
    # topic_dialog = get_dialog_chain(topic_data, speaker0, speaker1)

    return topic_dialog

# ОКОНЧАНИЕ ВАРИАНТ 2
##############################

#%%

dataset = []
for file in dataset_files[-1:]:
    df_topics = pd.read_csv(file)
    df_topics = df_topics.drop(['topic_name'], axis=1) # 'html', 'author_name', 'url'
#%%
    print('Файл', file)
    print('Стурктура данных\n', df_topics.info())
    print('Пример данных\n', df_topics.head())
    print('Уникальных топиков', len(df_topics['topic_id'].unique()))
    topic_ids = df_topics['topic_id'].unique()
    print('Состав топиков', len(topic_ids))
    # %%
    for id in topic_ids:
        topic_data = df_topics[df_topics['topic_id'] == id]
        print(f'Количество сообщений в топике {id}: {len(topic_data)}')
        # Вариант цепочек 1
        # topic_dialog = dialog_chain_variant1(topic_data)
        # if topic_data is None:
        #     continue
        # %%
        # Вариант цепочек 2
        topic_data = df_topics[df_topics['topic_id'] == 16]
        print(topic_data['url'])
        print(topic_data)
        topic_dialog = dialog_chain_variant2(topic_data)
        # %%
        # if topic_data is None:
        #     continue

        # tpdl = pd.DataFrame(topic_dialog)
        # print(tpdl.info())
        # print(tpdl)
        # print(topic_dialog)

        # topic_dataset = prepare_to_dialog_format(topic_dialog)
        # print(topic_dataset[0],'###\n')
        # print(topic_dataset[1],'###\n')

        # dataset.extend(topic_dataset)





#%%
# pprint.pprint(dataset)
# print(dataset[0],'###\n')
# print(dataset[1],'###\n')

# Сохраняем датасет
df_dataset = pd.DataFrame(dataset)
print(df_dataset)
df_topics = df_dataset.to_csv(TCV_FILE, header=False, index=False)


#%%
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
  ###Присоединяюсь к вопросу. И, пожалуйста, по содержанию. Коль уж Вы так любите самоутверждаться - нет проблем, но и содержание
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
  ####text 2
</div>
"""
post_sel = Selector(text=html1)
# quot2 = post_sel.xpath('//div[@class="text"]/div[@class="forum_quote"]')[1].get()
# quot1 = post_sel.xpath('//div[@class="text"]/div[@class="forum_quote"]')[0].get()
text_all = post_sel.xpath('.//div[@class="text"]/following-sibling').extract()

    #.get_all()
print(text_all)
