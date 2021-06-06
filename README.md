# Подготовка датасетов

## Предварительная установка
```
conda install -c conda-forge scrapy
# или
pip install scrapy-pyppeteer
```

## Парсинг форумов
* https://psy.su/club/forum/
    * проверка `scrapy check psy_su`
    * скрапинг `scrapy crawl psy_su`
    * результат в файле `data/data_psy_su.csv`
* https://psyhelp24.org
    * проверка `scrapy check psyhelp24_org`
    * скрапинг `scrapy crawl psyhelp24_org`
    * результат в файле `data/data_psyhelp24_org.csv`
* https://psycheforum.ru
    * проверка `scrapy check psycheforum_ru`
    * скрапинг `scrapy crawl psycheforum_ru`
    * результат в файле `data/data_psycheforum_ru.csv`
 
* https://www.b17.ru/forum/
* https://forum.psyche.guru/
* https://www.psychologies.ru/forum/ (закрыт)

Тестовый запуск на получение 5 записей `scrapy crawl psycheforum_ru -s CLOSESPIDER_ITEMCOUNT=5`

## Предварительная поготовка датасета на основе спарсеных файлов

Подготовку выполняет скрипт `prepare4db.py`.

Запуск `python prepare4db.py`
