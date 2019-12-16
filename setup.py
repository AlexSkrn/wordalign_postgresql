import os

from playhouse.postgres_ext import fn

from model import db
from model import TranslationUnits
from model import Gloss

# db.connect()
db.create_tables([TranslationUnits, Gloss])

# data = [('I love (Python)', 'Я люблю (Python)'),
#         ('I hate Python', 'Я терпеть не могу Python'),
#         ('I love coding', 'Мне нравится писать код'),
#         ('I like C++', 'Мне нравится C++')
#         ]
###########################################################################
units_data = []
with open(os.path.join('data', 'en_ru_sorted_uniq_desimil'), 'r', encoding='utf8') as fromF:
    for line in fromF:
        line_list = line.split('\t')
        src, trg = line_list[0].strip(), line_list[1].strip()
        row = (src, fn.to_tsvector(src),
               trg, fn.to_tsvector(trg)
               )
        units_data.append(row)

unit_fields = [TranslationUnits.eng_content, TranslationUnits.eng_search,
               TranslationUnits.rus_content, TranslationUnits.rus_search]
with db.atomic():
    TranslationUnits.insert_many(units_data, fields=unit_fields).execute()
###########################################################################
# def insert_data(src, trg):
#     record = TranslationUnits.create(eng_content=src,
#                                      eng_search=fn.to_tsvector(src),
#                                      rus_content=trg,
#                                      rus_search=fn.to_tsvector(trg)
#                                      )
#
# # NEED TO CHANGE THIS FOR BULK INSERT SOMEHOW!
# for en, ru in data:
#     insert_data(en, ru)

########
# units_data = []
# for src, trg in data:
#     row = (src, fn.to_tsvector(src),
#            trg, fn.to_tsvector(trg)
#            )
#     units_data.append(row)
# unit_fields = [TranslationUnits.eng_content, TranslationUnits.eng_search,
#                TranslationUnits.rus_content, TranslationUnits.rus_search]
# with db.atomic():
#     TranslationUnits.insert_many(units_data, fields=unit_fields).execute()

# Enter data into Glossary
# gloss_data = [('i', 'я'),
#               ('love', 'люблю'),
#               ('love', 'нравится'),
#               ('python', 'python'),
#               ('hate', 'терпеть'),
#               ('hate', 'не'),
#               ('hate', 'могу'),
#               ('like', 'нравится'),
#               ('c', 'c'),
#               ('coding', 'писать'),
#               ('coding', 'код'),
#               ]
#
# fields = [Gloss.eng_term, Gloss.rus_term]
# with db.atomic():
#     Gloss.insert_many(gloss_data, fields=fields).execute()


gloss_data = []
with open(os.path.join('data', 'lex_preproc40_cleaned'), 'r', encoding='utf8') as fromF:
    for line in fromF:
        line_list = line.split('\t')
        src, trg = line_list[0].strip(), line_list[1].strip()
        gloss_data.append((src, trg))

fields = [Gloss.eng_term, Gloss.rus_term]
with db.atomic():
    Gloss.insert_many(gloss_data, fields=fields).execute()
