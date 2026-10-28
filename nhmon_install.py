"""Intégration des monstres du projet dans les sources de NetHack.

Chaque ajout est repérable (« nhmonedit » en commentaire) : une nouvelle
intégration retire d'abord la précédente, et « retirer » rend les
fichiers dans leur état d'origine.

Fichiers touchés (chemins relatifs aux sources) :
  include/monsters.h        entrée MON() à la fin de la classe choisie
  src/makemon.c             PV fixes des golems (golemhp())
  win/share/monsters.txt    tuiles mâle et femelle (interfaces graphiques)
  po/fr.po, po/themes/fr@cyber.po, po/nethack.pot
                            nom français et genre grammatical
  dat/data.base, dat/data-fr.base, dat/data-fr@cyber.base
                            encyclopédie (commande « ; » ou « / »)
  include/patchlevel.h      EDITLEVEL + 1 si la liste des monstres change
                            (les anciennes sauvegardes deviennent invalides)
"""

import os
import re
import subprocess
import shutil
import time

import nhmon_data as D
from nhmon_i18n import _
import nhmon_templates as T

TAG = "nhmonedit"
MONSTERS_H = "include/monsters.h"
MAKEMON_C = "src/makemon.c"
TILES = "win/share/monsters.txt"
PO_FILES = ["po/fr.po", "po/themes/fr@cyber.po", "po/nethack.pot"]
DATA_FILES = {"dat/data.base": "encyclo_en",
              "dat/data-fr.base": "encyclo_fr",
              "dat/data-fr@cyber.base": "encyclo_fr"}
PATCHLEVEL = "include/patchlevel.h"
FIXES = "doc/fixes5-0-0.txt"
ALL_FILES = [MONSTERS_H, MAKEMON_C, TILES, PATCHLEVEL] + PO_FILES \
    + list(DATA_FILES) + [FIXES]
# l'entrée de doc/fixes, reconnue à son début (pas de marqueur dans la
# documentation du jeu)
FIXES_PREFIX = "new monsters made with nhmonedit: "


class InstallError(Exception):
    pass


def _read(src, rel):
    with open(os.path.join(src, rel), encoding="utf-8") as f:
        return f.read()


def _write(src, rel, text):
    path = os.path.join(src, rel)
    tmp = path + ".nhmonedit-tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


def check_tree(src):
    """Message d'erreur si src n'est pas un arbre de sources NetHack."""
    if not os.path.isfile(os.path.join(src, MONSTERS_H)):
        return _("Pas de %s dans %s") % (MONSTERS_H, src)
    return None


# --- retrait ------------------------------------------------------------

BEGIN_RE = re.compile(r"^[ \t]*/\* %s:begin (\w+) \*/\n.*?"
                      r"^[ \t]*/\* %s:end \1 \*/\n" % (TAG, TAG),
                      re.M | re.S)
TXT_BEGIN_RE = re.compile(r"^# %s:begin (\S+)\n.*?^# %s:end \1\n"
                          % (TAG, TAG), re.M | re.S)
LINE_TAG = "/* %s */" % TAG


def strip_monsters_h(text):
    return BEGIN_RE.sub("", text)


def strip_lines(text):
    """Retire les lignes marquées « /* nhmonedit */ » (makemon.c)."""
    return "".join(l for l in text.splitlines(True) if LINE_TAG not in l)


def strip_txt(text):
    return TXT_BEGIN_RE.sub("", text)


def strip_po(text):
    """Retire les entrées .po précédées du commentaire « # nhmonedit »."""
    blocks = re.split(r"\n\n+", text)
    keep = [b for b in blocks
            if not re.match(r"^# %s: " % TAG, b.lstrip("\n"))]
    out = "\n\n".join(keep)
    return out if out.endswith("\n") else out + "\n"


def installed_ids(src):
    """Identifiants des monstres de l'éditeur présents dans monsters.h."""
    try:
        text = _read(src, MONSTERS_H)
    except OSError:
        return []
    return re.findall(r"/\* %s:begin (\w+) \*/" % TAG, text)


def game_monsters(src):
    """Monstres du jeu sans ceux ajoutés par l'éditeur."""
    text = strip_monsters_h(_read(src, MONSTERS_H))
    out = []
    for _s, _e, args in D.iter_mon_calls(text):
        if len(args) == 14 and args[0].startswith("NAM"):
            out.append(D.parse_mon(args))
    return out


# --- insertion dans monsters.h -------------------------------------------

def _class_end_positions(text):
    """{S_classe: (position après la dernière entrée du premier bloc de la
    classe, nom de ce dernier monstre)}. Le premier bloc s'arrête au
    premier monstre d'une autre classe : la règle 1 de monsters.h (classes
    contiguës) est respectée, et les monstres « spéciaux » de fin de liste
    (rôles, PM_LONG_WORM_TAIL et suivants) ne sont pas concernés."""
    out, closed, prev = {}, set(), None
    for _s, e, args in D.iter_mon_calls(text):
        if len(args) != 14 or not args[0].startswith("NAM"):
            continue
        sym = args[1]
        if sym != prev:
            if prev is not None:
                closed.add(prev)
            prev = sym
        if sym in closed:
            continue            # deuxième bloc de la même classe
        out[sym] = (text.index("\n", e) + 1, D.parse_mon(args)["name"])
    return out


def _entry_end(text, name):
    """Position après l'entrée MON() du monstre name, ou None."""
    for _s, e, args in D.iter_mon_calls(text):
        if len(args) == 14 and args[0].startswith("NAM") and \
                D.parse_mon(args)["name"] == name:
            return text.index("\n", e) + 1
    return None


def _name_before(text, pos):
    """Nom du dernier monstre dont l'entrée finit avant pos."""
    prev = None
    for _s, e, args in D.iter_mon_calls(text):
        if e >= pos:
            break
        if len(args) == 14 and args[0].startswith("NAM"):
            prev = D.parse_mon(args)["name"]
    return prev


def insert_monsters_h(text, monsters):
    """Texte de monsters.h avec les monstres (déjà nettoyé), et l'ordre
    final : liste de (nom du monstre précédent, monstre). Un monstre va
    à la fin de sa classe, ou après le monstre de son champ « after »."""
    anchors = []
    for m in monsters:
        ends = _class_end_positions(text)
        if m["sym"] not in ends:
            raise InstallError(_("Classe %s absente de monsters.h : un "
                               "monstre ne peut pas ouvrir une nouvelle "
                               "classe ici") % m["sym"])
        pos, prev = ends[m["sym"]]
        if m.get("after"):
            pos = _entry_end(text, m["after"])
            if pos is None:
                raise InstallError(_("« %s » introuvable dans monsters.h "
                                     "(placer « %s » après)") % (
                                         m["after"], m["name"]))
        # après des blocs de l'éditeur : on les garde devant (ordre du
        # projet)
        while True:
            tail = re.match(r"[ \t]*/\* %s:end \w+ \*/\n" % TAG,
                            text[pos:])
            if tail:
                pos += tail.end()
                continue
            blk = re.match(r"[ \t]*/\* %s:begin (\w+) \*/\n.*?"
                           r"^[ \t]*/\* %s:end \1 \*/\n" % (TAG, TAG),
                           text[pos:], re.S | re.M)
            if not blk:
                break
            pos += blk.end()
        prev = _name_before(text, pos)
        block =("    /* %s:begin %s */\n" % (TAG, m["bn"])
                 + D.c_entry(m, marker=False) + "\n"
                 + "    /* %s:end %s */\n" % (TAG, m["bn"]))
        text = text[:pos] + block + text[pos:]
        anchors.append((prev, m))
    return text, anchors


# --- golemhp() ----------------------------------------------------------

def insert_golemhp(text, monsters):
    golems = [m for m in monsters if m["sym"] == "S_GOLEM"]
    if not golems:
        return text
    mo = re.search(r"^golemhp\(int type\)\n\{.*?^(    default:\n)", text,
                   re.M | re.S)
    if not mo:
        raise InstallError(_("golemhp() introuvable dans %s") % MAKEMON_C)
    add = "".join("    case PM_%s: %s\n        return %d; %s\n"
                  % (m["bn"], LINE_TAG, m["golem_hp"], LINE_TAG)
                  for m in golems)
    return text[:mo.start(1)] + add + text[mo.start(1):]


# --- tuiles -------------------------------------------------------------

TILE_HDR = re.compile(r"^# (tile|placeholder) (\d+) \((.*)\)$", re.M)


def tile_block(m):
    rows = "".join("  %s\n" % r for r in T.tile_for(m))
    out = "# %s:begin %s\n" % (TAG, m["bn"])
    for g in ("male", "female"):
        out += "# tile 0 (%s,%s)\n{\n%s}\n" % (m["name"], g, rows)
    return out + "# %s:end %s\n" % (TAG, m["bn"])


def insert_tiles(text, anchors, known):
    """known : noms de tous les monstres de mons[]. Les tuiles qui suivent
    l'ancre sans être dans mons[] (monstres désactivés que tilemap.c garde
    à leur place, comme « beholder ») restent collées à l'ancre."""
    nxt = re.compile(r"# tile \d+ \((.*),male\)\n\{\n.*?^\}\n"
                     r"# tile \d+ \(\1,female\)\n\{\n.*?^\}\n",
                     re.M | re.S)
    for prev, m in anchors:
        mo = re.search(r"^# tile \d+ \(%s,female\)\n\{\n.*?^\}\n"
                       % re.escape(prev), text, re.M | re.S)
        if not mo:
            raise InstallError(_("Tuile de « %s » introuvable dans %s")
                               % (prev, TILES))
        end = mo.end()
        # après un bloc de l'éditeur, on reste après sa ligne de fin
        tail = re.match(r"# %s:end \S+\n" % TAG, text[end:])
        if tail:
            end += tail.end()
        while True:
            mo = nxt.match(text, end)
            if not mo or mo.group(1) in known:
                break
            end = mo.end()
        text = text[:end] + tile_block(m) + text[end:]
    return renumber_tiles(text)


def renumber_tiles(text):
    count = [0]

    def num(mo):
        n = count[0]
        count[0] += 1
        return "# %s %d (%s)" % (mo.group(1), n, mo.group(3))
    return TILE_HDR.sub(num, text)


# --- traductions ---------------------------------------------------------

def _po_str(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def po_entries(m, kind):
    """Entrées .po d'un monstre ; kind : « fr », « cyber » ou « pot »."""
    pairs = [(m["name"], m["fr_name"])]
    if m["name_m"]:
        pairs += [(m["name_m"], m["fr_name_m"]), (m["name_f"], m["fr_name_f"])]
    out = []
    for en, fr in pairs:
        if kind != "pot" and not fr:
            continue
        if kind == "pot":
            name_tr = gender = ""
        else:
            name_tr = fr
            g = m["fr_gender"]
            if en == m["name_f"] and en:
                g = "f"
            elif en == m["name_m"] and en:
                g = "m"
            # fr.po : masculin vide ; thème : « m » explicite (sinon c'est
            # le genre de fr.po qui serait repris)
            gender = g if (g == "f" or kind == "cyber") else ""
        ctxs = [("monster", name_tr), ("gender", gender)]
        # pluriel corrigé à la main : dans le thème seulement, comme les
        # autres exceptions « monster-plural » (fr.po n'en a pas)
        if kind == "cyber" and en == m["name"] and m["fr_plural"].strip():
            ctxs.append(("monster-plural", m["fr_plural"].strip()))
        for ctx, val in ctxs:
            out.append("# %s: %s\nmsgctxt \"%s\"\nmsgid %s\nmsgstr %s"
                       % (TAG, m["bn"], ctx, _po_str(en), _po_str(val)))
    return out


def insert_po(text, monsters, kind):
    entries = []
    for m in monsters:
        entries += po_entries(m, kind)
    if not entries:
        return text
    return text.rstrip("\n") + "\n\n" + "\n\n".join(entries) + "\n"


# --- encyclopédie -------------------------------------------------------

def _wrap_text(text, width=64):
    lines = []
    for para in text.strip().split("\n"):
        words, cur = para.split(), ""
        if not words:
            lines.append("")
            continue
        for w in words:
            if cur and len(cur) + 1 + len(w) > width:
                lines.append(cur)
                cur = w
            else:
                cur = cur + " " + w if cur else w
        lines.append(cur)
    return lines


def data_block(m, field):
    text = m[field] or (m["encyclo_fr"] if field == "encyclo_en" else "")
    if not text.strip():
        return ""
    body = "".join(("\t%s\n" % l) if l else "\n" for l in _wrap_text(text))
    keys = [m["name"].lower()]
    keys += [n.lower() for n in (m["name_m"], m["name_f"]) if n]
    return ("# %s:begin %s\n%s\n%s# %s:end %s\n"
            % (TAG, m["bn"], "\n".join(keys), body, TAG, m["bn"]))


def insert_data(text, monsters, field):
    """Entrées placées avant la première entrée du fichier : la recherche
    prend la première clé qui correspond, une clé exacte doit donc passer
    avant les jokers (« *golem »)."""
    blocks = "".join(data_block(m, field) for m in monsters)
    if not blocks:
        return text
    mo = re.search(r"^[^#\s]", text, re.M)
    pos = mo.start() if mo else len(text)
    return text[:pos] + blocks + text[pos:]


# --- EDITLEVEL ----------------------------------------------------------

def bump_editlevel(text):
    mo = re.search(r"^#define EDITLEVEL (\d+)", text, re.M)
    if not mo:
        raise InstallError(_("EDITLEVEL introuvable dans %s") % PATCHLEVEL)
    n = int(mo.group(1)) + 1
    return text[:mo.start(1)] + str(n) + text[mo.end(1):], n


# --- opérations ----------------------------------------------------------

def backup(src, backup_root):
    """Copie les fichiers touchés dans backup_root/<date>/. Renvoie le
    dossier."""
    dest = os.path.join(backup_root, time.strftime("%Y%m%d-%H%M%S"))
    for rel in ALL_FILES:
        p = os.path.join(src, rel)
        if os.path.isfile(p):
            q = os.path.join(dest, rel)
            os.makedirs(os.path.dirname(q), exist_ok=True)
            shutil.copy2(p, q)
    return dest


def list_backups(backup_root):
    """[(dossier, fichiers relatifs)] des sauvegardes, la plus récente
    d'abord."""
    out = []
    try:
        names = sorted(os.listdir(backup_root), reverse=True)
    except OSError:
        return out
    for n in names:
        d = os.path.join(backup_root, n)
        files = [rel for rel in ALL_FILES
                 if os.path.isfile(os.path.join(d, rel))]
        if os.path.isdir(d) and files:
            out.append((d, files))
    return out


def restore_plan(src, backup_dir):
    """{fichier relatif: texte sauvegardé} des fichiers qui diffèrent des
    sources."""
    out = {}
    for rel in ALL_FILES:
        p = os.path.join(backup_dir, rel)
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as f:
                text = f.read()
            if not os.path.isfile(os.path.join(src, rel)) or \
                    _read(src, rel) != text:
                out[rel] = text
    return out


# --- doc/fixes5-0-0.txt --------------------------------------------------

def default_fixes(monsters):
    """Texte proposé pour l'entrée de doc/fixes (après FIXES_PREFIX)."""
    return ", ".join("%s (%s)" % (m["name"], m["fr_name"])
                     if m["fr_name"] else m["name"] for m in monsters)


def fixes_entry(text):
    """Texte de l'entrée de l'éditeur dans doc/fixes, ou None."""
    mo = re.search(r"^%s(.*\n(?:\t.*\n)*)" % re.escape(FIXES_PREFIX), text,
                   re.M)
    if not mo:
        return None
    return " ".join(mo.group(1).split())


def strip_fixes(text):
    return re.sub(r"^%s.*\n(?:\t.*\n)*" % re.escape(FIXES_PREFIX), "",
                  text, flags=re.M)


def wrap_fixes(body):
    """Entrée coupée comme celles du fichier : 78 colonnes, suite des
    lignes en retrait d'une tabulation."""
    lines, cur = [], FIXES_PREFIX.rstrip()
    for word in body.split():
        width = 78 if not lines else 70
        if len(cur) + 1 + len(word) > width:
            lines.append(cur)
            cur = "\t" + word
        else:
            cur += " " + word
    return "\n".join(lines + [cur]) + "\n"


def insert_fixes(text, body):
    """Ajoute l'entrée à la fin de « General New Features »."""
    if not body.strip():
        return text
    head = text.find("\nGeneral New Features\n")
    nxt = text.find("\n\n\n", head) if head >= 0 else -1
    if nxt < 0:
        raise InstallError(_("Section « General New Features » introuvable "
                             "dans %s") % FIXES)
    pos = nxt + 1
    return text[:pos] + wrap_fixes(body) + text[pos:]


def plan(src, monsters, fixes=""):
    """Nouveaux textes des fichiers : {chemin relatif: texte}. Ne touche
    à rien sur le disque. fixes : texte de l'entrée de doc/fixes (vide :
    pas d'entrée)."""
    out = {}
    old_h = _read(src, MONSTERS_H)
    clean_h = strip_monsters_h(old_h)
    new_h, anchors = insert_monsters_h(clean_h, monsters)
    out[MONSTERS_H] = new_h
    out[MAKEMON_C] = insert_golemhp(strip_lines(_read(src, MAKEMON_C)),
                                    monsters)
    if os.path.isfile(os.path.join(src, TILES)):
        known = {D.parse_mon(a)["name"]
                 for _s, _e, a in D.iter_mon_calls(new_h)
                 if len(a) == 14 and a[0].startswith("NAM")}
        out[TILES] = insert_tiles(renumber_tiles(
            strip_txt(_read(src, TILES))), anchors, known)
    for rel, kind in zip(PO_FILES, ("fr", "cyber", "pot")):
        if os.path.isfile(os.path.join(src, rel)):
            out[rel] = insert_po(strip_po(_read(src, rel)), monsters, kind)
    for rel, field in DATA_FILES.items():
        if os.path.isfile(os.path.join(src, rel)):
            out[rel] = insert_data(strip_txt(_read(src, rel)), monsters,
                                   field)
    if os.path.isfile(os.path.join(src, FIXES)):
        out[FIXES] = insert_fixes(strip_fixes(_read(src, FIXES)),
                                  fixes if monsters else "")
    return out


def _mon_signature(text):
    """Liste ordonnée des identifiants : change quand mons[] change."""
    return [a[13] for _s, _e, a in D.iter_mon_calls(text) if len(a) == 14]


def apply(src, files, bump=True, backup_root=None):
    """Écrit les fichiers prévus. Renvoie (fichiers modifiés, nouveau
    EDITLEVEL ou None, dossier de sauvegarde ou None)."""
    old_h = _read(src, MONSTERS_H)
    changed = [rel for rel, t in files.items() if _read(src, rel) != t]
    newlevel = None
    if bump and MONSTERS_H in files and \
            _mon_signature(old_h) != _mon_signature(files[MONSTERS_H]):
        files = dict(files)
        files[PATCHLEVEL], newlevel = bump_editlevel(_read(src, PATCHLEVEL))
        changed.append(PATCHLEVEL)
    if not changed:
        return [], None, None
    saved = backup(src, backup_root) if backup_root else None
    for rel in changed:
        _write(src, rel, files[rel])
    return changed, newlevel, saved


# --- git -----------------------------------------------------------------

def _git(src, *args):
    try:
        r = subprocess.run(["git", "-C", src] + list(args),
                           capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as e:
        return False, str(e)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def is_git_repo(src):
    return _git(src, "rev-parse", "--is-inside-work-tree")[0]


def commit_message(monsters):
    """Message proposé pour le commit des sources."""
    if not monsters:
        return "Remove the monsters added with nhmonedit"
    names = ", ".join(m["name"] for m in monsters)
    return ("Add monster%s made with nhmonedit: %s"
            % ("s" if len(monsters) > 1 else "", names))


def git_commit(src, paths, message):
    """Commit des seuls fichiers donnés (ce qui est déjà indexé à côté
    n'est pas emporté). Renvoie (réussi, sortie de git)."""
    ok, out = _git(src, "add", "--", *paths)
    if not ok:
        return ok, out
    return _git(src, "commit", "-m", message, "--only", "--", *paths)


def install(src, monsters, bump=True, backup_root=None, fixes=""):
    return apply(src, plan(src, monsters, fixes), bump, backup_root)


def uninstall(src, bump=True, backup_root=None):
    return install(src, [], bump, backup_root)


def diff(src, files):
    """Différences (format unifié) entre les sources et les textes
    prévus."""
    import difflib
    out = []
    for rel, new in files.items():
        old = _read(src, rel)
        if old != new:
            out += difflib.unified_diff(
                old.splitlines(True), new.splitlines(True),
                "a/" + rel, "b/" + rel, n=2)
    return "".join(out)
