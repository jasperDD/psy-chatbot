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
    if file.endswith('.csv') and file in ['data_psy_su.csv', 'data_psyhelp24_org.csv', 'data_b17_ru-1.csv', 'data_psycheforum_ru-1.csv']:
        dataset_files.append(os.path.join(DATA_PATH, file))

print('Список файлов датасетов', dataset_files)

#%%
##############################
# ВАРИАНТ 2 создания цепочек диалогов
def get_quotes(post):
    post_sel = Selector(text=post['html'])
    topic_dialog = []
    if 'psy.su' in post['url']:
        # TODO откидывает оформленный текст, т.к. он внутри текста um, em, b и т.д. https://psy.su/club/forum/topic/16/?page=2
        # TODO 2 вначале сообщения до цитаты откидывает текс, можно бы возвращать как текст о твет на предыдущий диалог - т.е. обычная цепочка.
        quotes_all = post_sel.xpath('//div[@class="text"]/div[@class="forum_quote"]/div[@class="quote"]/text()').getall()
        text_all = post_sel.xpath('.//div[@class="text"]/text()').getall()
        if text_all and quotes_all:
            if len(text_all) > len(quotes_all):
                text_all = text_all if text_all[0].strip() else text_all[1:]  # Первый текст до цитат пропускаем
            for quote, text in zip(quotes_all, text_all):  # Лишнюю дилну откидываем
                topic_dialog.append((quote.translate(character_map).strip(), text.translate(character_map).strip()))
    elif 'b17.ru' in post['url']:
        quotes_all = post_sel.xpath('//td[@class="mes qq"]/div[@class="quote"]')  # TODO вложенные цитаты тоже вытаскивает как текст
        text_all = post_sel.xpath('//td[@class="mes qq"]//text()').getall()
        text_all = [x.strip() for x in text_all if x.strip()] # Чистим от пустых строк
        try:
            for idx, quote in enumerate(quotes_all):
                quote_arr = quote.xpath('.//text()').getall()
                quote_arr = [x.strip() for x in quote_arr if 'писал(а)' not in x and x.strip()]  # Удаляем загловки цитаты и пустые элементы
                if not quote_arr:
                    continue
                quote_res = '\n'.join(quote_arr)
                text_start_idx = text_all.index(quote_arr[len(quote_arr) - 1]) + 1  # TODO возможно не уникальный текст в цитате или вообще пустая, лучше проверять все значения цитаты
                text_end_idx = len(text_all)
                for i, el in enumerate(text_all[text_start_idx:]):
                    if 'писал(а)' in el:
                        text_end_idx = text_start_idx + i
                        break
                text_res = '\n'.join(text_all[text_start_idx: text_end_idx])
                topic_dialog.append((quote_res.translate(character_map).strip(), text_res.translate(character_map).strip()))
        except Exception as err:
            print(err)
            print('Пост', post['author_id'], post['url'], post['url'], post['html'])
    elif 'psycheforum.ru' in post['url']:
        quotes_all = post_sel.xpath('//div[@data-role="commentContent"]/blockquote')  # TODO вложенную цитаты вытаскивает как текст
        text_all = post_sel.xpath('//div[@data-role="commentContent"]//p//text()').getall()
        text_all = [x.strip() for x in text_all if x.strip()]

        for idx, quote in enumerate(quotes_all):
            quote_arr = quote.xpath('.//p//text()').getall()
            quote_arr = [x.strip() for x in quote_arr if x.strip()]  # Удаляем пустые тексты
            if not quote_arr:
                continue
            quote_res = '\n'.join(quote_arr)
            text_start_idx = None
            for txt_idx, text in enumerate(text_all):  # Ищем индекс в тексте окончания цитаты
                if quote_arr[
                    len(quote_arr) - 1] in text:  # TODO возможно не уникальный текст в цитате или вообще пустая, лучше проверять все значения цитаты
                    text_start_idx = txt_idx + 1 if txt_idx + 1 < len(
                        text_all) else None  # Если после цитаты еще есть текст, если нет то это нет ответа
                    break
            if text_start_idx is None:  # Если в текстах не нашли последнюю фразу цитаты, пропускаем
                continue
            text_end_idx = len(text_all)
            next_quote = quotes_all[idx + 1] if idx + 1 < len(quotes_all) else None
            if next_quote is not None:
                next_quote_arr = next_quote.xpath('.//p//text()').getall()
                next_quote_arr = [x.strip() for x in next_quote_arr if x.strip()]  # Удаляем пустые тексты
                if next_quote_arr:  # Если следующая цитата не пустая # TODO пустая, но например за ней текст? Или еще цитата?
                    next_quote_val = next_quote_arr[0]
                    for i, el in enumerate(text_all[text_start_idx:]):
                        if next_quote_val == el: # Нашли начало следующей цитаты
                            text_end_idx = text_start_idx + i
                            break
            text_res = '\n'.join(text_all[text_start_idx: text_end_idx])
            topic_dialog.append((quote_res.translate(character_map).strip(), text_res.translate(character_map).strip()))
    if topic_dialog and len(topic_dialog):
        return topic_dialog
    return None

#%%
def dialog_chain_variant2(topic_data):
    topic_starter_id  = topic_data['author_id'].iloc[0]
    if topic_starter_id is None:
        return None
    topic_dialog = []
    dialog_part = {topic_starter_id: str(topic_data['text'].iloc[0]).strip()} # Считаем, что первое сообщение не может быть с цитатой
    for idx, post in topic_data[1:].iterrows(): # Перую пропускаем
        quotes_dialog = get_quotes(post)
        if quotes_dialog is not None: # Если сообщение содержит цитирование, тогда добавляем все пары цитата и ответ как отдельные цепочки, в цеопчки сообщений не учитываем
             topic_dialog.extend(quotes_dialog)
             continue
             # TODO а если цитаты у автора? По идее это запуск новой цепочки
             # TODO Еще могут быть цитаты не на автора, а других участников - это запуск новой цепочки
        elif post['text'] and type(post['text']) == str: # Если в сообщении нет цитат, то тогда рассматирваем его целиком в цепочке
            text = post['text'].translate(character_map).strip()
            author_id = post['author_id']
            if author_id == topic_starter_id: # Если автор топикстартер - то это начало новой цепочки или добавление к предыдущей, если других авторов еще нет
                if len(dialog_part) > 1:  # Ключей больше чем 1, т.е. есть диалог
                    authors_all = [author for author in dialog_part.keys() if author != topic_starter_id]
                    # print('authors_all', authors_all)
                    for author in authors_all[:min(5, len(authors_all))]: # Обрываем длину цепочек не более 5ти, т.к. больше вероятней это уже обсуждение без автора, TODO формирование новой цепочки
                        topic_dialog.append((dialog_part[topic_starter_id], dialog_part[author]))
                    dialog_part = {topic_starter_id: text}
                    # print('Новая цепочка', dialog_part)
                else:  # Ключ пока 1, т.е. это автор разместил последующий за своим пост, просто суммируем
                    dialog_part[topic_starter_id] += text
            else:
                if not dialog_part.get(author_id): # Если нет более раннего сообщения, иначе пропускаем (МОЖНО СУММИРОВАТЬ, но это более вероятно могут быть ответы к постам других авторов)
                    dialog_part[author_id] = text
        # TODO подумать, если ответов автора давно не было, т.е. дискусия носит общий характер и все отвечают друг-другу.
        #   Возможно тогда логика должна учтиывать ответы других авторов и перезапускать цепочки уже от них. Выявлять
        #   чередования и т.д. - более сложная логика, или смотреть на даты сообщений

    return topic_dialog

# ОКОНЧАНИЕ ВАРИАНТ 2
##############################

#%%

dataset = []
for file in dataset_files: # [:1]
    print('Файл', file)
    df_topics = pd.read_csv(file, dtype=str)
    df_topics = df_topics.drop(['topic_name'], axis=1) # 'html', 'author_name', 'url'
    # TODO при парсинге могил возникнуть дублеты сообщений, нужно почистить
    # TODO имеет смысл добавить столбец с последовательностью всех постов
    # TODO в соответствии с логикой урл для страниц по каждому форуму - нужно отсортировать все топики по этим страницам,
    #  а в них по добавленному столбцу порядка сообщений. Т.к. во время парсинга, старницы могли скачиваться не последовательно (!)
#%%
    print('Стурктура данных\n', df_topics.info())
    print('Пример данных\n', df_topics.head())
    topic_ids = df_topics['topic_id'].unique() # Идентификаторы топиков
    topic_ids_list = list(topic_ids)
    print('Уникальных топиков', len(topic_ids))

#%%
    for id in topic_ids:
        if id == 'topic_id': # Если код топика равен названию столбца топика - это строки заголовков добавленные scrapy при возобновлении парсинга
            continue
#%%
        topic_data = df_topics[df_topics['topic_id'] == id]
        # Вариант цепочек 1
        # topic_dialog = dialog_chain_variant1(topic_data)
        # if topic_data is None:
        #     continue
        # %%
        # Вариант цепочек 2 # 2del# topic_data = df_topics[df_topics['topic_id'] == 16]
        # print(topic_data)
        topic_dialog = dialog_chain_variant2(topic_data)
        print(f'{file}: Топик {id} сообщений {len(topic_data)} -> цепочек {len(topic_dialog)},',
              f'{topic_ids_list.index(id)/len(topic_ids_list) * 100:.1f}%')
        if len(topic_data) == 0:
            print(f'В топике {topic_data["url"].iloc[0]} 0 цепочек')
        # for val in topic_dialog:
        #     print(val)

        # %%
        if topic_data is None:
            continue

        # tpdl = pd.DataFrame(topic_dialog)
        # print(tpdl.info())
        # print(tpdl)
        # print(topic_dialog)

        topic_dataset = prepare_to_dialog_format(topic_dialog)
        # print(topic_dataset[0],'###\n')
        # print(topic_dataset[1],'###\n')

        dataset.extend(topic_dataset)
    print(f'После файла {file} длина датасета {len(dataset)}')
    print(dataset[-5:])



#%%
# Сохраняем датасет
df_dataset = pd.DataFrame(dataset)
print(df_dataset)
df_topics = df_dataset.to_csv(TCV_FILE, header=False, index=False)


