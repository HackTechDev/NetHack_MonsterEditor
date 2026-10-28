"""Fichiers de l'éditeur : projets (liste de monstres en JSON), fusion
de projets, monstres exportés un par un (*.nhmon.json), sauvegarde de
secours (projet.json.nhmonedit-autosave), modèles personnels
(~/.config/nhmonedit/modeles.json)."""

import json
import os

import nhmon_data as D
from nhmon_i18n import _

PROJECT_FORMAT = "nhmonedit"
MONSTER_FORMAT = "nhmonedit-monstre"
MONSTER_SUFFIX = ".nhmon.json"
AUTOSAVE_SUFFIX = ".nhmonedit-autosave"
AUTOSAVE_DELAY = 60         # secondes
TEMPLATES_FORMAT = "nhmonedit-modeles"
CONFIG_DIR = os.path.join(os.environ.get("XDG_CONFIG_HOME") or
                          os.path.expanduser("~/.config"), "nhmonedit")


def templates_path():
    return os.environ.get("NHMONEDIT_TEMPLATES") or \
        os.path.join(CONFIG_DIR, "modeles.json")


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


def export_path(directory, m):
    """Fichier d'export d'un monstre : <identifiant>.nhmon.json."""
    return os.path.join(directory, m["bn"].lower() + MONSTER_SUFFIX)


def write_monster(path, m):
    write_json(path, {"format": MONSTER_FORMAT, "version": 1,
                      "monster": m})


def read_monsters(path):
    """Monstres d'un projet ou d'un monstre exporté, complétés par
    normalize()."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise ProjectError(_("%s illisible : %s") % (path, e))
    fmt = data.get("format") if isinstance(data, dict) else None
    if fmt == MONSTER_FORMAT and isinstance(data.get("monster"), dict):
        return [D.normalize(data["monster"])]
    if fmt != PROJECT_FORMAT:
        raise ProjectError(_("%s n'est pas un projet nhmonedit") % path)
    return [D.normalize(m) for m in data.get("monsters", [])]


def autosave_path(project):
    return project + AUTOSAVE_SUFFIX


def pending_autosave(project):
    """Sauvegarde de secours plus récente que le projet (session
    interrompue), ou None ; une sauvegarde périmée est effacée."""
    auto = autosave_path(project)
    if not os.path.isfile(auto):
        return None
    if os.path.isfile(project) and \
            os.path.getmtime(auto) <= os.path.getmtime(project):
        drop_autosave(project)
        return None
    return auto


def drop_autosave(project):
    try:
        os.remove(autosave_path(project))
    except OSError:
        pass


def read_templates(path):
    """Modèles personnels : [(nom, description, monstre)] ; fichier
    absent : liste vide."""
    if not os.path.isfile(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise ProjectError(_("%s illisible : %s") % (path, e))
    if not isinstance(data, dict) or data.get("format") != TEMPLATES_FORMAT:
        raise ProjectError(_("%s n'est pas un fichier de modèles") % path)
    return [(t.get("name", "?"), t.get("description", ""),
             D.normalize(t.get("monster", {})))
            for t in data.get("templates", [])]


def write_templates(path, templates):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    write_json(path, {"format": TEMPLATES_FORMAT, "version": 1,
                      "templates": [{"name": n, "description": d,
                                     "monster": m}
                                    for n, d, m in templates]})


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
