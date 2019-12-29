import os

from playhouse.postgres_ext import Model
from playhouse.postgres_ext import TextField
from playhouse.postgres_ext import TSVectorField

from playhouse.db_url import connect

db = connect(os.environ.get('DATABASE_URL') or 'postgresql://alex:@localhost:5432/my_app')


class TranslationUnits(Model):
    eng_content = TextField()
    eng_search = TSVectorField()

    rus_content = TextField()
    rus_search = TSVectorField()

    class Meta:
        database = db


class Gloss(Model):
    eng_term = TSVectorField()
    rus_term = TextField()
    suggest_eng = TextField(null=True)  # Keeps an autocomplete list

    class Meta:
        database = db
