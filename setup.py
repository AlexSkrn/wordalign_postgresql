import os

from playhouse.postgres_ext import fn

from model import db
from model import TranslationUnits
from model import Gloss

db.drop_tables([TranslationUnits, Gloss])
db.create_tables([TranslationUnits, Gloss])

###########################################################################
# FILLING IN TRANSLATION SEGMENTS DATA
units_data = []
with open(os.path.join('data', 'en_ru_heroku_1000'), 'r', encoding='utf8') as fromF:
    for line in fromF:
        line_list = line.split('\t')
        src, trg = line_list[0].strip(), line_list[1].strip()
        row = (src, fn.to_tsvector(src),
               trg, fn.to_tsvector('russian', trg)
               )
        units_data.append(row)

unit_fields = [TranslationUnits.eng_content, TranslationUnits.eng_search,
               TranslationUnits.rus_content, TranslationUnits.rus_search]
with db.atomic():
    TranslationUnits.insert_many(units_data, fields=unit_fields).execute()

###########################################################################
# FILLING IN GLOSSARY DATA
gloss_data = []
with open(os.path.join('data', 'heroku_glossary'), 'r', encoding='utf8') as fromF:
    for line in fromF:
        line_list = line.split('\t')
        src, trg = line_list[0].strip(), line_list[1].strip()
        row = [src, fn.to_tsvector(src),
               trg, fn.to_tsvector('russian', trg)
               ]
        gloss_data.append(row)

# Fill in autocomplete column
gloss_autocomplete_data = []
with open(os.path.join('data', 'auto_complete_eng'), 'r', encoding='utf8') as fromF:
    for line in fromF:
        term = line.strip()
        gloss_autocomplete_data.append(term)

with open(os.path.join('data', 'auto_complete_rus'), 'r', encoding='utf8') as fromF:
    for line in fromF:
        term = line.strip()
        gloss_autocomplete_data.append(term)

gloss_autocomplete_data.sort(key=lambda x: len(x), reverse=True)


for idx, item in enumerate(gloss_data):
    try:
        gloss_data[idx].append(gloss_autocomplete_data[idx])
    except IndexError:
        gloss_data[idx].append(None)

fields = [Gloss.eng_term_content, Gloss.eng_term_search,
          Gloss.rus_term_content, Gloss.rus_term_search,
          Gloss.suggest_eng]

with db.atomic():
    Gloss.insert_many(gloss_data, fields=fields).execute()
