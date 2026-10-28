"""Langue de l'interface : français (langue des sources) ou anglais.

La langue est choisie à l'importation, avant que les autres modules ne
construisent leurs textes : $NHMONEDIT_LANG (fr ou en), sinon la locale
(LANGUAGE, LC_ALL, LC_MESSAGES, LANG) : français si elle commence par
« fr », anglais sinon.

Les textes sont écrits en français dans le code et passent par _() ;
leur traduction est dans nhmon_i18n_en.py (texte absent : laissé en
français). Les noms français des monstres, le code C et les textes
écrits dans les sources du jeu ne sont pas traduits.
"""

import os


def detect():
    lang = os.environ.get("NHMONEDIT_LANG", "").lower()
    if lang in ("fr", "en"):
        return lang
    for var in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        v = os.environ.get(var)
        if v:
            return "fr" if v.lower().startswith("fr") else "en"
    return "en"


LANG = detect()
_CATALOG = {}
if LANG == "en":
    from nhmon_i18n_en import EN as _CATALOG


def _(text):
    """Texte traduit dans la langue de l'interface."""
    return _CATALOG.get(text, text)
