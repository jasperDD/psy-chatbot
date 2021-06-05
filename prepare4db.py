#%%
import os
import pandas as pd
# import numpy as np
# import random
import pprint
import re
from transformers import AutoTokenizer # AutoModelForCausalLM,

#%%
MODEL_PATH='./model'
MODEL_CACHE='./model-cache'


if not os.path.exists(MODEL_PATH):
    MODEL_NAME = 'sberbank-ai/rugpt3small_based_on_gpt2'
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, cache_dir=MODEL_CACHE)
else:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)

#%%
def get_pair_of_speaker(topic):
    speaker0 = topic['author_id'].iloc[0]
    speaker1 = None
    for author_id in topic['author_id']:
        if author_id != speaker0:
            speaker1 = author_id
            break
    return speaker0, speaker1

# TODO не выстраивает логику ответов в обсужданиях, считает что ответ идет на предыдущий пост, а не например на последующие
# посты. Не учитывает, что на часть постов отвечал другой и что второй автор может отвечать на посты других авторов.
# Нужно строить деревья ответов.
def get_dialog_chain(topic, speaker0: str, speaker1: str) -> list:
    cur_speaker = speaker0
    cur_sentence = ''
    cur_chain_cell = []
    dialog = []
    topic_filtered = topic[topic['author_id'].isin([speaker0, speaker1])]
    # topic_filtered = topic_filtered.drop_duplicates(subset='text') # TODO надо править в парсере, чтобы не парсил несколько раз одну страницу - парсер нормальный, дописывал файл при нескольких запусках.
    # print('chain\n')
    # pprint.pprint(topic_filtered)
    character_map = {
        ord(' '): ' ',
        ord('\n'): ' ',
        ord('\t'): ' ',
        ord('\r'): None
    }

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

def get_length_param(text: str) -> str:
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

def prepare_to_dialog_format(dialog: list) -> list:
    topic_dataset = []
    for row in dialog:
        spk0_len = get_length_param(row[0])
        spk1_len = get_length_param(row[1])
        dialog_str = f'|0|{spk0_len}|{row[0]}|1|{spk1_len}|{row[1]}'
        topic_dataset.append(dialog_str)
    return topic_dataset
#%%
DATA_PATH='./data'

dataset_files = []
for file in os.listdir(DATA_PATH):
    if file.endswith('.csv'):
        dataset_files.append(os.path.join(DATA_PATH, file))

print(dataset_files)



#%%

dataset = []
for file in dataset_files:
    data = pd.read_csv(file)
    data = data.drop(['html', 'url', 'author_name', 'topic_name'], axis=1)
#%%
    print('Файл', file)
    print('Стурктура данных\n', data.info())
    print('Пример данных\n', data.head())
    print('Уникальных топиков', len(data['topic_id'].unique()))
    topics = data['topic_id'].unique()
    print(topics)
    # %%
    for topic_id in topics:
        print('topic_id', topic_id)
        topic_data = data[data['topic_id'] == topic_id]
        # print('Фильтрованные данные по топику\n', topic_data[['topic_id', 'author_id', 'text']].head())
        speaker0, speaker1 = get_pair_of_speaker(topic_data)
        if speaker1 is None:
            continue
        print(speaker0, speaker1, len(topic_data))
        topic_dialog = get_dialog_chain(topic_data, speaker0, speaker1)
        # tpdl = pd.DataFrame(topic_dialog)
        # print(tpdl.info())
        # print(tpdl)
        # print(topic_dialog)
        topic_dataset = prepare_to_dialog_format(topic_dialog)
        # print(topic_dataset[0],'###\n')
        # print(topic_dataset[1],'###\n')
        dataset.extend(topic_dataset)





#%%
# pprint.pprint(dataset)
# print(dataset[0],'###\n')
# print(dataset[1],'###\n')

TCV_FILE='./data/dataset.tsv'
df_dataset = pd.DataFrame(dataset)
print(df_dataset)
data = df_dataset.to_csv(TCV_FILE, header=False, index=False)

# data_path = "twitter_sentiment_corpus.csv"

