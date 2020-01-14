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


def get_segments(search_list):
    # Collect possible Russian translations
    # Exact search
    exact_search_rus_terms = []
    for eng_term in search_list:
        rus_query = (Gloss.select(Gloss.rus_term_content)
                     .where(Gloss.eng_term_search == eng_term)  # Exact query
                     )
        rus_terms_cur = db.execute(rus_query)  # 'люблю | нравится'
        for t in rus_terms_cur:
            exact_search_rus_terms.append(t[0])
    # Fuzzy search
    # # eng_terms = fn.to_tsquery(eng_terms)  # No need because
    # using .match in where clause invokes to_tsquery() and, thus, FTS
    eng_terms = ' | '.join(search_list)   # -> 'love | python'
    fuzzy_search_rus_terms = []
    rus_query = (Gloss.select(Gloss.rus_term_content)
                 .where(Gloss.eng_term_search.match(eng_terms))  # Fuzzy query
                 )
    rus_terms_cur = db.execute(rus_query)
    for t in rus_terms_cur:
        fuzzy_search_rus_terms.append(t[0])

    # Combine search results
    exact_search_rus_terms.extend(fuzzy_search_rus_terms)
    rus_terms = set(exact_search_rus_terms)

    rus_terms = ' | '.join(rus_terms)  # 'люблю | нравится | python'

    TranslationUnitsAlias = TranslationUnits.alias()
    subquery = (TranslationUnitsAlias.select(
                              TranslationUnitsAlias.eng_content,
                              TranslationUnitsAlias.rus_content,
                              fn.ts_rank_cd(TranslationUnitsAlias.eng_search, fn.to_tsquery(eng_terms)).alias('rnk')
                                            )
                   .where(TranslationUnitsAlias.eng_search.match(eng_terms))
                   .limit(50)
                   )
    query = (TranslationUnits.select(
                fn.ts_headline(subquery.c.eng_content,
                               fn.to_tsquery(eng_terms),
                               # 'StartSel=<mark><b>, StopSel=</mark></b>',
                               'HighlightAll=TRUE',
                               ),
                fn.ts_headline(subquery.c.rus_content,
                               fn.to_tsquery(rus_terms),
                               # 'StartSel=<mark><b>, StopSel=</mark></b>'),
                               'HighlightAll=TRUE',
                               )
                                    )
                   .from_(subquery)
                   .order_by(subquery.c.rnk.desc())
                   .limit(10)
                   )
    rec = db.execute(query)
    results = []
    for line in rec:
        line0, line1 = re.sub('<b>', '<mark><b>', line[0]), \
                       re.sub('<b>', '<mark><b>', line[1])
        line0, line1 = re.sub('</b>', '</b></mark>', line0), \
                       re.sub('</b>', '</b></mark>', line1)
        results.append((line0, line1))
    return results, eng_terms


def get_segments_rus(search_list):
    # Collect possible Russian translations
    # Exact search
    exact_search_eng_terms = []
    for rus_term in search_list:
        eng_query = (Gloss.select(Gloss.eng_term_content)
                     .where(Gloss.rus_term_search == rus_term)  # Exact query
                     )
        eng_terms_cur = db.execute(eng_query)  # 'люблю | нравится'
        for t in eng_terms_cur:
            exact_search_eng_terms.append(t[0])
    # Fuzzy search
    # # eng_terms = fn.to_tsquery(eng_terms)  # No need because
    # using .match in where clause invokes to_tsquery() and, thus, FTS
    rus_terms = ' | '.join(search_list)   # -> 'love | python'
    fuzzy_search_eng_terms = []
    eng_query = (Gloss.select(Gloss.eng_term_content)
                 .where(Gloss.rus_term_search.match(rus_terms))  # Fuzzy query
                 )
    eng_terms_cur = db.execute(eng_query)
    for t in eng_terms_cur:
        fuzzy_search_eng_terms.append(t[0])

    # Combine search results
    exact_search_eng_terms.extend(fuzzy_search_eng_terms)
    eng_terms = set(exact_search_eng_terms)

    eng_terms = ' | '.join(eng_terms)  # 'люблю | нравится | python'

    TranslationUnitsAlias = TranslationUnits.alias()
    subquery = (TranslationUnitsAlias.select(
                              TranslationUnitsAlias.rus_content,
                              TranslationUnitsAlias.eng_content,
                              fn.ts_rank_cd(TranslationUnitsAlias.rus_search, fn.to_tsquery(rus_terms)).alias('rnk')
                                            )
                   .where(TranslationUnitsAlias.rus_search.match(rus_terms))
                   .limit(50)
                   )
    query = (TranslationUnits.select(
                fn.ts_headline(subquery.c.rus_content,
                               fn.to_tsquery(rus_terms),
                               # 'StartSel=<mark><b>, StopSel=</mark></b>',
                               'HighlightAll=TRUE',
                               ),
                fn.ts_headline(subquery.c.eng_content,
                               fn.to_tsquery(eng_terms),
                               # 'StartSel=<mark><b>, StopSel=</mark></b>'),
                               'HighlightAll=TRUE',
                               )
                                    )
                   .from_(subquery)
                   .order_by(subquery.c.rnk.desc())
                   .limit(10)
                   )
    rec = db.execute(query)
    results = []
    for line in rec:
        line0, line1 = re.sub('<b>', '<mark><b>', line[0]), \
                       re.sub('<b>', '<mark><b>', line[1])
        line0, line1 = re.sub('</b>', '</b></mark>', line0), \
                       re.sub('</b>', '</b></mark>', line1)
        results.append((line0, line1))
    return results, rus_terms


@app.route('/retrieve')
def retrieve():
    search_term = request.args.get('search_term')
    if not search_term:
        return render_template("retrieve.jinja2")
    else:
        # try:
        search_term_res = ''
        for symb in search_term.lower():
            if symb not in '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~':
                search_term_res += symb
        search_term_res_list4 = search_term_res.split()[:4]
        if any(ltr in string.ascii_lowercase for ltr in search_term_res_list4[0]):
            results, terms = get_segments(search_term_res_list4)
        else:
            # print('invoking elif clause!!!')
            results, terms = get_segments_rus(search_term_res_list4)

##########################################################################
        # # Collect possible Russian translations
        # # Exact search
        # exact_search_rus_terms = []
        # for eng_term in search_term_res_list4:
        #     rus_query = (Gloss.select(Gloss.rus_term)
        #                  .where(Gloss.eng_term == eng_term)  # Exact query
        #                  )
        #     rus_terms_cur = db.execute(rus_query)  # 'люблю | нравится'
        #     for t in rus_terms_cur:
        #         exact_search_rus_terms.append(t[0])
        # # Fuzzy search
        # # # eng_terms = fn.to_tsquery(eng_terms)  # No need because
        # # using .match in where clause invokes to_tsquery() and, thus, FTS
        # eng_terms = ' | '.join(search_term_res_list4)   # -> 'love | python'
        # fuzzy_search_rus_terms = []
        # rus_query = (Gloss.select(Gloss.rus_term)
        #              .where(Gloss.eng_term.match(eng_terms))  # Fuzzy query
        #              )
        # rus_terms_cur = db.execute(rus_query)
        # for t in rus_terms_cur:
        #     fuzzy_search_rus_terms.append(t[0])
        #
        # # Combine search results
        # exact_search_rus_terms.extend(fuzzy_search_rus_terms)
        # rus_terms = set(exact_search_rus_terms)
        #
        # rus_terms = ' | '.join(rus_terms)  # 'люблю | нравится | python'
        #
        # TranslationUnitsAlias = TranslationUnits.alias()
        # subquery = (TranslationUnitsAlias.select(
        #                           TranslationUnitsAlias.eng_content,
        #                           TranslationUnitsAlias.rus_content,
        #                           fn.ts_rank_cd(TranslationUnitsAlias.eng_search, fn.to_tsquery(eng_terms)).alias('rnk')
        #                                         )
        #                .where(TranslationUnitsAlias.eng_search.match(eng_terms))
        #                .limit(50)
        #                )
        # query = (TranslationUnits.select(
        #             fn.ts_headline(subquery.c.eng_content,
        #                            fn.to_tsquery(eng_terms),
        #                            # 'StartSel=<mark><b>, StopSel=</mark></b>',
        #                            'HighlightAll=TRUE',
        #                            ),
        #             fn.ts_headline(subquery.c.rus_content,
        #                            fn.to_tsquery(rus_terms),
        #                            # 'StartSel=<mark><b>, StopSel=</mark></b>'),
        #                            'HighlightAll=TRUE',
        #                            )
        #                                 )
        #                .from_(subquery)
        #                .order_by(subquery.c.rnk.desc())
        #                .limit(10)
        #                )
        # rec = db.execute(query)
        # results = []
        # for line in rec:
        #     line0, line1 = re.sub('<b>', '<mark><b>', line[0]), \
        #                    re.sub('<b>', '<mark><b>', line[1])
        #     line0, line1 = re.sub('</b>', '</b></mark>', line0), \
        #                    re.sub('</b>', '</b></mark>', line1)
        #     results.append((line0, line1))
    ##########################################################################
        if len(results) > 0:
            return render_template("retrieve.jinja2", results=results, terms=terms)
        else:
            return render_template("retrieve.jinja2", no_res="No results found", terms=terms)


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
