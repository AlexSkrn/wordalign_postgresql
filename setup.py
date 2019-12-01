from playhouse.postgres_ext import fn

from model import db
from model import TranslationUnits
from model import Gloss

# db.connect()
db.create_tables([TranslationUnits, Gloss])

data = [ ('I love Python', 'Я люблю Python'),
        ('I hate Python', 'Я терпеть не могу Python'),
        ('I love coding', 'Мне нравится писать код'),
        ('I like C++', 'Мне нравится C++')
        ]


def insert_data(src, trg):
    record = TranslationUnits.create(eng_content=src,
                                     eng_search=fn.to_tsvector(src),
                                     rus_content=trg,
                                     rus_search=fn.to_tsvector(trg)
                                     )

# NEED TO CHANGE THIS FOR BULK INSERT SOMEHOW!
for en, ru in data:
    insert_data(en, ru)

fields = [Gloss.eng_term, Gloss.rus_term]

gloss_data = [('i', 'я'),
              ('love', 'люблю'),
              ('love', 'нравится'),
              ('python', 'python'),
              ('hate', 'терпеть'),
              ('hate', 'не'),
              ('hate', 'могу'),
              ('like', 'нравится'),
              ('c', 'c'),
              ('coding', 'писать'),
              ('coding', 'код'),
              ]

with db.atomic():
    Gloss.insert_many(gloss_data, fields=fields).execute()
