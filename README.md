# Подготовка датасетов

## Предварительная установка
```
pip install scrapy-pyppeteer
pip install beautifulsoup4
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
    * проверка что работает `scrapy check psycheforum_ru`
    * просмотр выдачи со странички `scrapy parse --spider=psycheforum_ru https://psycheforum.ru/topic/97703-lyubovnaya-addikciya/`  
    * скрапинг `scrapy crawl psycheforum_ru`
    * скрапинг с сохранением и возможностью продолжить при остановке 
      `scrapy crawl psycheforum_ru -s JOBDIR=crawls/psycheforum_ru-1`
    * результат в файле `data/data_psycheforum_ru.csv`
* https://www.b17.ru/forum/
  * проверка `scrapy check b17_ru`
  * получение данных с одной странички `scrapy parse -s spider=b17_ru --depth=1 https://www.b17.ru/forum/topic.php?id=365771`
  * скрапинг `scrapy crawl b17_ru`
  * данные в файле `data/data_b17_ru.csv`
* https://forum.psyche.guru/
* https://www.psychologies.ru/forum/ (закрыт)

Тестовый запуск на получение 5 записей `scrapy crawl psycheforum_ru -s CLOSESPIDER_ITEMCOUNT=5`

## Предварительная поготовка датасета на основе спарсеных файлов

Подготовку выполняет скрипт `prepare4db.py`.

Запуск `python prepare4db.py`
