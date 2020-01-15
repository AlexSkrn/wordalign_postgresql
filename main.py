# # This query works in psql
# """SELECT ts_headline('english', eng_content, to_tsquery('love | python'))
# FROM (SELECT eng_content, rus_content
# FROM translationunits
# WHERE to_tsvector(eng_content) @@ to_tsquery('love | python')
# AND  to_tsvector(rus_content) @@ to_tsquery('люблю | нравится')) as s"""


###############
import os

import re
import string

from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import jsonify
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


@app.route('/google49522071f37de87c.html')
def google_verify():
    """Return google verification code page."""
    return render_template('googleverify.jinja2')


def format_highlight(executed_query):
    results = []
    new_opening_tag = '<mark><b>'
    new_closing_tag = '</b></mark>'
    # '/retrieve?search_term=Соединенные+Штаты+Америки'
    pattern = r'<b>(\w+)</b>'

    for line in executed_query:
        trg_terms = '+'.join(set(re.findall(pattern, line[1])))
        new_trg_opening_tag = '<a href="/retrieve?search_term={}" rel="nofollow">{}'.format(trg_terms, new_opening_tag)
        new_trg_closing_tag = '{}</a>'.format(new_closing_tag)
        line0, line1 = re.sub('<b>', new_opening_tag, line[0]), \
                       re.sub('<b>', new_trg_opening_tag, line[1])
        line0, line1 = re.sub('</b>', new_closing_tag, line0), \
                       re.sub('</b>', new_trg_closing_tag, line1)
        results.append((line0, line1))
    return results


def query_gloss(search_list, FTS_search_str, lang):
    """Return a string of target terms found."""
    if lang == 'english':
        trg_term_content = Gloss.rus_term_content
        src_term_search = Gloss.eng_term_search
    if lang == 'russian':
        trg_term_content = Gloss.eng_term_content
        src_term_search = Gloss.rus_term_search
    # Collect possible search term translations
    target_terms = []
    # Exact search
    for term in search_list:
        query = (Gloss.select(trg_term_content)
                 .where(src_term_search == term)
                 )
        cur = db.execute(query)
        for t in cur:
            target_terms.append(t[0])
    # Fuzzy search
    query = (Gloss.select(trg_term_content)
             .where(src_term_search.match(FTS_search_str, language=lang))
             )
    cur = db.execute(query)
    for t in cur:
        target_terms.append(t[0])

    return ' | '.join(set(target_terms))  # -> 'like | love | python'


def query_eng(FTS_src_str, FTS_trg_str):
    TranslationUnitsAlias = TranslationUnits.alias()
    subquery = (TranslationUnitsAlias.select(
                              TranslationUnitsAlias.eng_content,
                              TranslationUnitsAlias.rus_content,
                              # fn.ts_rank_cd(TranslationUnitsAlias.eng_search, fn.to_tsquery(FTS_search_str)).alias('rnk')
                                            )
                   .where(TranslationUnitsAlias.eng_search.match(FTS_src_str))
                   .order_by(fn.ts_rank_cd(TranslationUnitsAlias.eng_search, fn.to_tsquery(FTS_src_str)).desc())
                   .limit(10)
                   )
    query = (TranslationUnits.select(
                fn.ts_headline(subquery.c.eng_content,
                               fn.to_tsquery(FTS_src_str),
                               # 'StartSel=<mark><b>, StopSel=</mark></b>',
                               'HighlightAll=TRUE',
                               ),
                fn.ts_headline(subquery.c.rus_content,
                               fn.to_tsquery(FTS_trg_str),
                               # 'StartSel=<mark><b>, StopSel=</mark></b>'),
                               'HighlightAll=TRUE',
                               )
                                    )
                   .from_(subquery)
                   # .order_by(subquery.c.rnk.desc())
                   # .limit(10)
                   )
    rec = db.execute(query)
    return format_highlight(rec)


def query_rus(FTS_src_str, FTS_trg_str):
    TranslationUnitsAlias = TranslationUnits.alias()
    subquery = (TranslationUnitsAlias.select(
                              TranslationUnitsAlias.rus_content,
                              TranslationUnitsAlias.eng_content,
                                            )
                 .where(TranslationUnitsAlias.rus_search.match(FTS_src_str, language='russian'))
                 .order_by(fn.ts_rank_cd(TranslationUnitsAlias.rus_search, fn.to_tsquery('russian', FTS_src_str)).desc())
                 .limit(10)
                )
    query = (TranslationUnits.select(
                fn.ts_headline('russian', subquery.c.rus_content,
                               fn.to_tsquery('russian', FTS_src_str),
                               'HighlightAll=TRUE',
                               ),
                fn.ts_headline(subquery.c.eng_content,
                               fn.to_tsquery(FTS_trg_str),
                               'HighlightAll=TRUE',
                               )
                                    )
             .from_(subquery)
             )
    rec = db.execute(query)
    return format_highlight(rec)


@app.route('/retrieve')
def retrieve():
    search_term = request.args.get('search_term')
    if not search_term:
        return render_template("retrieve.jinja2")
    else:
        search_term_res = ''
        for symb in search_term.lower():
            if symb not in '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~':
                search_term_res += symb
        search_term_res_list4 = search_term_res.split()[:4]
        FTS_search_str = ' | '.join(search_term_res_list4)
        try:
            if any(ltr in string.ascii_lowercase for ltr in search_term_res_list4[0]):
                trg_terms = query_gloss(search_term_res_list4, FTS_search_str, 'english')
                results = query_eng(FTS_search_str, trg_terms)
                # results = query_context(search_term_res_list4, FTS_search_str, 'english')

            else:
                trg_terms = query_gloss(search_term_res_list4, FTS_search_str, 'russian')
                results = query_rus(FTS_search_str, trg_terms)
                # results = query_context(search_term_res_list4, FTS_search_str, 'russian')
        except IndexError:
            return render_template("retrieve.jinja2", no_res="No results found")

        if len(results) > 0:
            return render_template("retrieve.jinja2", results=results, terms=FTS_search_str)
        else:
            return render_template("retrieve.jinja2", no_res="No results found", terms=FTS_search_str)


@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    search = request.args.get('q')
    q = (Gloss.select(Gloss.suggest_eng)
              .where(Gloss.suggest_eng.contains(search))
              .limit(15)
         )
    cur = db.execute(q)
    results = [elem[0] for elem in cur]

    return jsonify(matching_results=results)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 6738))
    # port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
