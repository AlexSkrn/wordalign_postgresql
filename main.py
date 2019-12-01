# from playhouse.postgres_ext import fn
#
# from model import db
# from model import TranslationUnits
#

# eng_terms = 'love | python'
# rus_terms = 'люблю | нравится'
#
#
# raw_query = (TranslationUnits.select(
#                              fn.ts_headline(TranslationUnits.eng_content, fn.to_tsquery(eng_terms)),
#                              fn.ts_headline(TranslationUnits.rus_content, fn.to_tsquery(rus_terms))
#                                     )
#                .where(TranslationUnits.eng_search.match(eng_terms))
#                .where(TranslationUnits.rus_search.match(rus_terms))
#                )
#
# rec = db.execute(raw_query)
# for r in rec:
#     print(r)
#
# # This query works in psql
# """SELECT ts_headline('english', eng_content, to_tsquery('love | python'))
# FROM (SELECT eng_content, rus_content
# FROM translationunits
# WHERE to_tsvector(eng_content) @@ to_tsquery('love | python')
# AND  to_tsvector(rus_content) @@ to_tsquery('люблю | нравится')) as s"""


###############
import os

from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
# from flask import session

from playhouse.postgres_ext import fn

from model import db
from model import TranslationUnits
from model import Gloss


app = Flask(__name__)

@app.route('/')
def home():
    """Handle calls to the root of the web site."""
    return redirect(url_for('retrieve'))

@app.route('/donations')
def show_all():
    """Handle a page showing all donors and donations."""
    # The code below gets results WITHOUT highlighting search terms
    query = (TranslationUnits
             .select()
             # .where(TranslationUnits.english.match('love'))
             # .where(TranslationUnits.russian.match('люблю OR нравится'))
             )
    rec = db.execute(query)
    return render_template('donations.jinja2', donations=rec)

@app.route('/retrieve')
def retrieve():
    code = request.args.get('code', None)
    if code is None:
        return render_template("retrieve.jinja2")
    else:
        try:
            num = len(code.split())
            eng_terms = ((' | '.join(['{}'] * num)).format(*code.split()))  # -> 'love | python'
            # eng_terms = fn.to_tsquery(eng_terms)
            rus_query = (Gloss.select(Gloss.rus_term)
                         .where(Gloss.eng_term.match(eng_terms))
                         )
            rus_terms_cur = db.execute(rus_query)
            rus_terms = []
            for t in rus_terms_cur:
                rus_terms.append(t[0])
            rus_terms = ' | '.join(rus_terms)  # 'люблю | нравится'

            query = (TranslationUnits.select(
                        fn.ts_headline(TranslationUnits.eng_content, fn.to_tsquery(eng_terms)),
                        fn.ts_headline(TranslationUnits.rus_content, fn.to_tsquery(rus_terms))
                                            )
                           .where(TranslationUnits.eng_search.match(eng_terms))
                           .where(TranslationUnits.rus_search.match(rus_terms))
                           )
        except TranslationUnits.DoesNotExist:
            return render_template("retrieve.jinja2", error="No results found")

        else:
            rec = db.execute(query)
            return render_template('showres.jinja2', donations=rec)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 6738))
    # port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
