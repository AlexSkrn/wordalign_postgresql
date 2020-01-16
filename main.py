import os

import string

from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import jsonify
# from flask import session

from dbqueries import query_gloss
from dbqueries import query_translations
from dbqueries import query_autocomplete


app = Flask(__name__)


@app.route('/')
def home():
    """Handle calls to the root of the web site."""
    return redirect(url_for('retrieve'))


@app.route('/google49522071f37de87c.html')
def google_verify():
    """Return google verification code page."""
    return render_template('googleverify.jinja2')


@app.route('/retrieve')
def retrieve():
    search_term = request.args.get('search_term')
    if not search_term:
        return render_template("retrieve.jinja2")
    else:
        search_term_res = ''
        for symb in search_term.lower():
            if symb not in r'!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~':
                search_term_res += symb
            else:
                search_term_res += ' '
        search_term_res_list4 = search_term_res.split()[:4]
        FTS_search_str = ' | '.join(search_term_res_list4)
        try:
            if any(ltr in string.ascii_lowercase for ltr in search_term_res_list4[0]):
                trg_terms = query_gloss(search_term_res_list4, FTS_search_str, 'english')
                results = query_translations(FTS_search_str, trg_terms, 'english')

            else:
                trg_terms = query_gloss(search_term_res_list4, FTS_search_str, 'russian')
                results = query_translations(FTS_search_str, trg_terms, 'russian')
        except IndexError:
            return render_template("retrieve.jinja2", no_res="No results found")

        if len(results) > 0:
            return render_template("retrieve.jinja2", results=results, terms=FTS_search_str)
        else:
            return render_template("retrieve.jinja2", no_res="No results found", terms=FTS_search_str)


@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    results = query_autocomplete(request.args.get('q'))
    return jsonify(matching_results=results)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 6738))
    # port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
