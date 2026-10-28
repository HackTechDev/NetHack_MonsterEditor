"""Fichiers de l'éditeur : projets (liste de monstres en JSON) et
fusion de projets."""

import json
import os

import nhmon_data as D
from nhmon_i18n import _

PROJECT_FORMAT = "nhmonedit"


class ProjectError(Exception):
    pass


def write_json(path, data):
    """Écrit le JSON par un fichier temporaire (pas de fichier à moitié
    écrit si l'écriture échoue)."""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")
    os.replace(tmp, path)


def write_project(path, monsters):
    write_json(path, {"format": PROJECT_FORMAT, "version": 1,
                      "monsters": monsters})


def read_monsters(path):
    """Monstres d'un fichier projet, complétés par normalize()."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise ProjectError(_("%s illisible : %s") % (path, e))
    if not isinstance(data, dict) or data.get("format") != PROJECT_FORMAT:
        raise ProjectError(_("%s n'est pas un projet nhmonedit") % path)
    return [D.normalize(m) for m in data.get("monsters", [])]


def same_monster(a, b):
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def json_files(dirs, suffix=".json"):
    """[(nom, dossier)] des fichiers *suffix des dossiers donnés."""
    out, seen = [], set()
    for d in dirs:
        try:
            names = sorted(os.listdir(d))
        except OSError:
            continue
        for n in names:
            p = os.path.realpath(os.path.join(d, n))
            if n.endswith(suffix) and os.path.isfile(p) and p not in seen:
                seen.add(p)
                out.append((n, d))
    return out
