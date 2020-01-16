"""Provide all db query functions."""
import re

from playhouse.postgres_ext import fn

from model import db
from model import TranslationUnits
from model import Gloss


def format_highlight(executed_query):
    """Provide custom tags to highlight query results."""
    results = []
    new_opening_tag = '<mark><b>'
    new_closing_tag = '</b></mark>'
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


def subquery_translations(FTS_src_str, lang):
    """Return ranked query results from TranslationUnits."""
    TranslationUnitsAlias = TranslationUnits.alias()
    if lang == 'english':
        src_content_field = TranslationUnitsAlias.eng_content
        trg_content_field = TranslationUnitsAlias.rus_content
        src_search_field = TranslationUnitsAlias.eng_search
    if lang == 'russian':
        src_content_field = TranslationUnitsAlias.rus_content
        trg_content_field = TranslationUnitsAlias.eng_content
        src_search_field = TranslationUnitsAlias.rus_search

    query = (TranslationUnitsAlias.select(src_content_field, trg_content_field)
             .where(src_search_field.match(FTS_src_str, language=lang))
             .order_by(fn.ts_rank_cd(src_search_field, fn.to_tsquery(lang, FTS_src_str)).desc())
             .limit(10)
             )
    return query


def query_translations(FTS_src_str, FTS_trg_str, src_lang):
    """Query TranslationUnits and return highlighted results."""
    if src_lang == 'english':
        trg_tang = 'russian'
        subquery = subquery_translations(FTS_src_str, src_lang)
        subq_src_content = subquery.c.eng_content
        subq_trg_content = subquery.c.rus_content
    if src_lang == 'russian':
        trg_tang = 'english'
        subquery = subquery_translations(FTS_src_str, src_lang)
        subq_src_content = subquery.c.rus_content
        subq_trg_content = subquery.c.eng_content

    query = (TranslationUnits.select(
                fn.ts_headline(src_lang, subq_src_content,
                               fn.to_tsquery(src_lang, FTS_src_str),
                               'HighlightAll=TRUE',
                               ),
                fn.ts_headline(trg_tang, subq_trg_content,
                               fn.to_tsquery(trg_tang, FTS_trg_str),
                               'HighlightAll=TRUE',
                               )
                                    )
             .from_(subquery)
             )
    rec = db.execute(query)
    return format_highlight(rec)


def query_autocomplete(search):
    """Query database autocomplete table."""
    q = (Gloss.select(Gloss.suggest_eng)
              .where(Gloss.suggest_eng.contains(search))
              .limit(15)
         )
    cur = db.execute(q)
    return [elem[0] for elem in cur]
