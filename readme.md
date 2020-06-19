# Поиск терминов в контексте на двух языках

Веб-сайт проекта: http://www.contextdict.com/

![screen_view](/images/screen_view.png)

Источник параллельного корпуса: ```https://conferences.unite.un.org/UNCorpus/```

Обработка текстов перед Word Alignment (см. https://github.com/AlexSkrn/wordalign_notebooks):

![chart](/images/preprocessing.png)

Word alignment и получение двуязычного глоссария:

![chart_2](/images/chart_2.png)

Хостинговый провайдер (Heroku) устанавливает ограничение в 10,000 строк базы данных для
бесплатных веб-сайтов. Поэтому для размещения данных и приложения на веб-сайте
я сократил текст до примерно 1 тысячи строк-предложений, а глоссарий до примерно 9 тысяч строк.

![chart_3](/images/chart_3.png)
