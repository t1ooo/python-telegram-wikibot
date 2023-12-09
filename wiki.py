from typing import Dict, List, Optional
import wikipedia


class WikiException(Exception):
    pass


def prepare_query(query: str) -> str:
    query = query.strip()
    if query == "":
        raise WikiException("Query is empty.")
    return query


def _init_langs() -> Dict[str, str]:
    langs = {}
    for code, lang in wikipedia.languages().items():
        langs[code] = code
        langs[lang.lower()] = code
    return langs


_LANGS = _init_langs()


def get_lang_code(lang: str) -> Optional[str]:
    return _LANGS.get(lang.lower())


_DEFAULT_LANG = "en"


def _set_lang(lang: str):
    lang = _LANGS.get(lang.lower(), _DEFAULT_LANG)
    wikipedia.set_lang(lang)


def search(query: str, lang: str) -> List[str]:
    query = prepare_query(query)
    _set_lang(lang)
    result = wikipedia.search(query) or []
    if len(result) == 0:
        raise WikiException(f"Nothing was found for the query {query}.")
    return result


def summary(query: str, lang: str) -> str:
    query = prepare_query(query)
    _set_lang(lang)
    try:
        return wikipedia.summary(query, auto_suggest=False) or ""
    except wikipedia.exceptions.DisambiguationError as e:
        raise WikiException(
            "\n".join(["Maybe you mean:"] + list(sorted(set(e.options))))
        )
    except wikipedia.exceptions.PageError as e:
        raise WikiException(f'Page with title "{query}" not found.')


def suggest(query: str, lang: str) -> str:
    query = prepare_query(query)
    _set_lang(lang)
    result = wikipedia.suggest(query) or ""
    if result == "":
        raise WikiException(f"No suggestion was found for the query {query}.")
    return result
