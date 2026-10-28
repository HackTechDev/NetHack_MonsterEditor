#!/usr/bin/env python3
"""nhmonedit — éditeur de monstres (robots et mechas) pour NetHack 5.0
cyberpunk, en mode terminal.

Usage : python3 nhmonedit.py [projet.json] [--src DOSSIER_DES_SOURCES]

Le projet (JSON) garde vos monstres ; « I » les intègre aux sources du
jeu (include/monsters.h, traductions, tuiles, encyclopédie), « m »
compile, « U » met à jour le jeu installé, « j » le lance en mode
wizard pour les essayer. Appuyez sur « ? » pour l'aide.
"""

import copy
import curses
import json
import os
import re
import shlex
import subprocess
import sys
import time

import nhmon_data as D
import nhmon_install as I
import nhmon_templates as T
from nhmon_ui import (Cancel, Colors, ESC, Popups, get_key, is_enter, put)

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PROJECT = os.path.join(HERE, "monstres.json")
DEFAULT_SRC = os.path.normpath(os.path.join(HERE, "..", "NetHack-5.0.0"))
BACKUP_DIR = os.path.join(HERE, "sauvegardes")
HACKDIRS = [
    os.environ.get("NHMONEDIT_HACKDIR", ""),
    os.path.expanduser("~/nh/install/games/lib/nethackdir"),
    os.path.join(DEFAULT_SRC, "playground"),
]

ALIGN_HINT = "négatif : chaotique, 0 : neutre, positif : loyal ; " \
             "-128 : sans alignement (A_NONE)"

# (type, clé, libellé, aide[, min, max, pas])
FIELDS = [
    ("section", None, "Identité", ""),
    ("text", "fr_name", "Nom français", "nom affiché dans le jeu "
     "(thème fr@cyber)"),
    ("choice", "fr_gender", "Genre (français)", "accord des phrases : "
     "« le », « la », « détruit », « détruite »"),
    ("plural", "fr_plural", "Pluriel français", "« trois mechas de "
     "combat » : vide = calculé par le jeu (s ou x à chaque mot avant "
     "« de », « à »…) ; Entrée pour le corriger"),
    ("text", "name", "Nom anglais", "nom interne du jeu (en minuscules) ; "
     "c'est lui qu'on tape avec ^G en mode wizard"),
    ("ident", "bn", "Identifiant PM_", "nom C : PM_<identifiant>, en "
     "majuscules"),
    ("text", "name_m", "  nom anglais masc.", "facultatif : nom propre au "
     "masculin (sinon le nom anglais sert pour tous)"),
    ("text", "name_f", "  nom anglais fém.", "facultatif : nom propre au "
     "féminin"),
    ("text", "fr_name_m", "  nom français masc.", "traduction du nom "
     "masculin"),
    ("text", "fr_name_f", "  nom français fém.", "traduction du nom "
     "féminin"),
    ("choice", "sym", "Classe", "lettre affichée sur la carte ; la classe "
     "golem (') donne des PV fixes, comme il sied à un robot"),
    ("choice", "color", "Couleur", "couleur de la lettre sur la carte"),
    ("section", None, "Caractéristiques", ""),
    ("int", "level", "Niveau", "niveau de base (0 à 49) : PV, toucher, "
     "profondeur d'apparition", 0, 49, 1),
    ("int", "move", "Vitesse", "12 = humain, 0 = immobile (tourelle), "
     "20+ = très rapide", 0, 127, 1),
    ("int", "ac", "Classe d'armure", "10 = sans armure, 0 = blindé, "
     "négatif = très blindé", -128, 127, 1),
    ("int", "mr", "Résist. magie %", "chance de résister aux sorts et "
     "baguettes (0 à 100)", 0, 127, 5),
    ("int", "align", "Alignement", ALIGN_HINT, -128, 127, 1),
    ("int", "golem_hp", "PV fixes (golem)", "seulement pour la classe "
     "golem (') : points de vie fixes (golem de fer : 120)", 1, 999, 5),
    ("difficulty", "difficulty", "Difficulté", "calculée comme le jeu "
     "(mstrength) ; Entrée pour forcer une valeur, vide = automatique"),
    ("section", None, "Génération", ""),
    ("int", "freq", "Fréquence", "0 = jamais au hasard … 7 = très "
     "courant (la plupart : 1 à 3)", 0, 7, 1),
    ("flags", "geno", "Drapeaux G_", "unique, groupes, génocide, "
     "cadavre…"),
    ("section", None, "Attaques", ""),
] + [("attack", i, "Attaque %d" % (i + 1), "Entrée : type, dégâts, dés ; "
      "Suppr : vider ; ←→ : changer le nombre de dés")
     for i in range(D.NATTK)] + [
    ("section", None, "Corps", ""),
    ("int", "weight", "Poids", "humain : 1450, golem de fer : 2000",
     0, 65535, 50),
    ("int", "nutrition", "Nutrition", "valeur nutritive du cadavre "
     "(0 pour une épave de robot)", 0, 65535, 50),
    ("choice", "sound", "Son", "bruit ou phrases du monstre (#parler)"),
    ("choice", "size", "Taille", "taille physique"),
    ("flags", "mr1", "Résistances", "résistances du monstre"),
    ("flags", "mr2", "Conférées", "résistances données en mangeant le "
     "cadavre"),
    ("flags", "flags1", "Drapeaux M1", "corps et déplacement"),
    ("flags", "flags2", "Drapeaux M2", "nature et comportement"),
    ("flags", "flags3", "Drapeaux M3", "divers (infravision, attente…)"),
    ("section", None, "Apparence et textes", ""),
    ("choice", "tile_shape", "Silhouette (tuile)", "image des versions "
     "graphiques (Qt, X11) seulement, invisible dans le terminal ; "
     "colorée d'après la couleur du monstre"),
    ("longtext", "encyclo_fr", "Encyclopédie (fr)", "texte de « ; » et "
     "« / » dans le jeu, en français"),
    ("longtext", "encyclo_en", "Encyclopédie (en)", "même texte en "
     "anglais (sinon le texte français est repris)"),
    ("longtext", "notes", "Notes", "vos notes (non intégrées au jeu)"),
]

HELP = [
    "nhmonedit — éditeur de monstres pour NetHack 5.0 cyberpunk",
    "",
    "Deux zones : la liste des monstres du projet (à gauche) et la fiche",
    "du monstre choisi. Tab passe de l'une à l'autre.",
    "",
    "Dans la fiche :",
    "  ↑ ↓          champ précédent / suivant",
    "  ← →          changer une valeur (nombre, choix, dés d'attaque)",
    "  Entrée       modifier le champ",
    "  Suppr        vider (attaque, texte)",
    "",
    "Monstres :",
    "  n            nouveau monstre d'après un modèle (robots, mechas…)",
    "  d            dupliquer le monstre",
    "  i            importer un monstre du jeu comme base",
    "  Suppr / X    supprimer le monstre (dans la liste)",
    "  < >          déplacer le monstre dans la liste",
    "  t            dessiner la tuile à la main (versions graphiques",
    "               seulement ; sinon la silhouette suffit)",
    "",
    "Contrôle :",
    "  v            vérifier tous les monstres",
    "  c            voir le code C (entrée MON() de monsters.h)",
    "  b            comparer aux monstres du jeu (difficulté proche)",
    "",
    "Sources du jeu :",
    "  I            intégrer les monstres aux sources (aperçu, puis",
    "               confirmation ; copie des fichiers dans sauvegardes/)",
    "  R            retirer les monstres des sources",
    "  m            compiler (make)",
    "  U            mettre à jour le jeu installé (make update : garde",
    "               sysconf, scores et sauvegardes)",
    "  j            lancer le jeu en mode wizard pour essayer",
    "",
    "Général :",
    "  s            enregistrer le projet",
    "  u            annuler la dernière modification",
    "  ?            cette aide       q  quitter",
    "",
    "En jeu (mode wizard) : Ctrl-G puis le nom ANGLAIS du monstre pour",
    "le créer à côté de vous ; « ; » pour le regarder (encyclopédie).",
    "",
    "Les nouveaux monstres changent la liste mons[] : l'intégration",
    "augmente EDITLEVEL (include/patchlevel.h), les anciennes sauvegardes",
    "et fichiers de bones ne se chargent plus.",
]


def align_label(v):
    if v == D.ALIGN_NONE:
        return "A_NONE (sans alignement)"
    if v < 0:
        return "%d (chaotique)" % v
    if v > 0:
        return "%d (loyal)" % v
    return "0 (neutre)"


def short_flags(names):
    return ", ".join(n.split("_", 1)[1] for n in names) if names else "—"


class Editor(Popups):
    def __init__(self, stdscr, project, src):
        self.stdscr = stdscr
        self.colors = Colors()
        self.project = project
        self.src = src
        self.monsters = []
        self.cur = 0
        self.field = 1
        self.focus = "list"
        self.modified = False
        self.undo_stack = []
        self.msg = ""
        self.form_top = 0
        self._game = None
        self._fr = None
        self._inst = (None, {})
        self.load()

    # --- données ----------------------------------------------------------

    def load(self):
        if os.path.isfile(self.project):
            with open(self.project, encoding="utf-8") as f:
                data = json.load(f)
            self.monsters = [D.normalize(m) for m in data.get("monsters", [])]
            self.msg = "Projet ouvert : %s (%d monstres)" % (
                self.project, len(self.monsters))
        else:
            self.monsters = []
            self.msg = "Nouveau projet : %s — « n » pour créer un " \
                       "monstre" % self.project

    def save(self):
        data = {"format": "nhmonedit", "version": 1,
                "monsters": self.monsters}
        tmp = self.project + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
            f.write("\n")
        os.replace(tmp, self.project)
        self.modified = False
        self.msg = "Enregistré : %s" % self.project

    def game(self):
        """Monstres du jeu (sans ceux de l'éditeur), lus une fois."""
        if self._game is None:
            try:
                self._game = I.game_monsters(self.src)
            except (OSError, ValueError):
                self._game = []
        return self._game

    def fr_names(self):
        if self._fr is None:
            self._fr = D.french_names(self.src)
        return self._fr

    def installed(self):
        """{identifiant: texte de l'entrée intégrée} (cache par date)."""
        path = os.path.join(self.src, I.MONSTERS_H)
        try:
            mt = os.path.getmtime(path)
        except OSError:
            return {}
        if self._inst[0] != mt:
            with open(path, encoding="utf-8") as f:
                text = f.read()
            blocks = {}
            for mo in re.finditer(r"/\* %s:begin (\w+) \*/\n(.*?)"
                                  r"^[ \t]*/\* %s:end \1 \*/" %
                                  (I.TAG, I.TAG), text, re.M | re.S):
                blocks[mo.group(1)] = mo.group(2).rstrip("\n")
            self._inst = (mt, blocks)
        return self._inst[1]

    def status(self, m):
        inst = self.installed()
        if m["bn"] not in inst:
            return "non intégré", curses.A_DIM
        if inst[m["bn"]] == D.c_entry(m, marker=False):
            return "intégré", self.colors.fg(curses.COLOR_GREEN, True)
        return "intégré, modifié depuis", \
            self.colors.fg(curses.COLOR_YELLOW, True)

    def mon(self):
        return self.monsters[self.cur] if self.monsters else None

    def others(self, m):
        return [o for o in self.monsters if o is not m]

    def checkpoint(self):
        self.undo_stack.append((copy.deepcopy(self.monsters), self.cur))
        del self.undo_stack[:-100]
        self.modified = True

    def undo(self):
        if not self.undo_stack:
            self.msg = "Rien à annuler"
            return
        self.monsters, self.cur = self.undo_stack.pop()
        self.cur = min(self.cur, max(0, len(self.monsters) - 1))
        self.modified = True
        self.msg = "Annulé"

    # --- dessin -----------------------------------------------------------

    def redraw(self):
        self.draw()

    def draw(self):
        scr = self.stdscr
        scr.erase()
        H, W = scr.getmaxyx()
        if H < 20 or W < 70:
            put(scr, 0, 0, "Terminal trop petit (70x20 minimum)")
            scr.refresh()
            return
        title = " nhmonedit ▸ robots & mechas de Night City "
        proj = " %s%s " % (os.path.basename(self.project),
                           " [modifié]" if self.modified else "")
        bar = self.colors.pair(curses.COLOR_BLACK, curses.COLOR_MAGENTA)
        put(scr, 0, 0, " " * W, bar)
        put(scr, 0, 0, title, bar | curses.A_BOLD)
        put(scr, 0, W - len(proj) - 1, proj, bar)
        lw = 30
        rw = 40 if W >= 120 else 0
        fw = W - lw - rw
        self.draw_list(1, 0, H - 3, lw)
        self.draw_form(1, lw, H - 3, fw)
        if rw:
            self.draw_side(1, lw + fw, H - 3, rw)
        # aide du champ et message
        m = self.mon()
        hint = ""
        if self.focus == "form" and m:
            hint = FIELDS[self.field][3]
        put(scr, H - 2, 0, (" " + hint).ljust(W),
            self.colors.fg(curses.COLOR_CYAN))
        keys = " n:nouveau d:dupl. i:importer v:vérif c:code b:comparer " \
               "I:intégrer m:make U:update j:jouer s:enreg. ?:aide q:quitter"
        put(scr, H - 1, 0, (" " + self.msg).ljust(W) if self.msg else
            keys.ljust(W), self.colors.pair(curses.COLOR_BLACK,
                                            curses.COLOR_CYAN))
        scr.refresh()

    def draw_list(self, y, x, h, w):
        scr = self.stdscr
        act = self.focus == "list"
        attr = self.colors.fg(curses.COLOR_MAGENTA, act)
        put(scr, y, x, "┌─ Monstres " + "─" * (w - 13) + "┐", attr)
        for i in range(1, h - 1):
            put(scr, y + i, x, "│", attr)
            put(scr, y + i, x + w - 1, "│", attr)
        put(scr, y + h - 1, x, "└" + "─" * (w - 2) + "┘", attr)
        if not self.monsters:
            put(scr, y + 2, x + 2, "(vide)", curses.A_DIM)
            put(scr, y + 3, x + 2, "n : nouveau monstre", curses.A_DIM)
            put(scr, y + 4, x + 2, "i : importer du jeu", curses.A_DIM)
            return
        rows = h - 2
        top = max(0, min(self.cur - rows // 2, len(self.monsters) - rows))
        for r, m in enumerate(self.monsters[top:top + rows]):
            i = top + r
            sel = i == self.cur
            a = curses.A_REVERSE if sel and act else \
                (curses.A_BOLD if sel else 0)
            ch = D.CLASS_CHAR.get(m["sym"], "?")
            put(scr, y + 1 + r, x + 1, " " * (w - 2), a)
            put(scr, y + 1 + r, x + 2, ch, self.colors.mon(m["color"]) |
                curses.A_BOLD | (a & curses.A_REVERSE))
            errs = any(g == "erreur" for g, _ in
                       D.validate(m, None, self.others(m)))
            name = m["fr_name"] or m["name"]
            put(scr, y + 1 + r, x + 4, name, a, w - 9)
            st, _sa = self.status(m)
            mark = "✖" if errs else ("●" if st == "intégré" else
                                     "◐" if st.startswith("intégré") else "")
            put(scr, y + 1 + r, x + w - 4, mark,
                self.colors.fg(curses.COLOR_RED, True) if errs else
                self.colors.fg(curses.COLOR_GREEN, True))

    def field_value(self, m, f):
        kind, key = f[0], f[1]
        if kind == "attack":
            at, ad, n, d = m["attacks"][key]
            if at == "AT_NONE" and ad == "AD_PHYS" and not n and not d:
                return "—", curses.A_DIM
            dice = "%dd%d" % (n, d) if n or d else "  "
            return "%-4s %-4s %-5s %s / %s" % (
                at[3:], ad[3:], dice, D.AT_DESC.get(at, "?"),
                D.AD_DESC.get(ad, "?")), 0
        v = m[key]
        if kind == "choice":
            if key == "fr_gender":
                return {"m": "masculin", "f": "féminin"}.get(v, v), 0
            if key == "tile_shape":
                if v == T.SHAPE_AUTO:
                    return "auto (%s, d'après la classe)" % T.shape_of(m), 0
                if v == T.SHAPE_CUSTOM:
                    return "personnalisée (dessinée avec t)", 0
                return v, 0
            if key == "sym":
                return "%s  %s" % (D.CLASS_CHAR.get(v, "?"), dict(
                    (s, d) for s, _c, d in D.CLASSES).get(v, v)), \
                    self.colors.mon(m["color"])
            if key == "color":
                return "%s (%s)" % (D.COLOR_FR.get(v, v), v), \
                    self.colors.mon(v) | curses.A_BOLD
            table = D.SOUNDS if key == "sound" else D.SIZES
            return "%s — %s" % (v, dict((n, d) for n, _x, d in table)
                                .get(v, "?")), 0
        if kind == "flags":
            return short_flags(v), (0 if v else curses.A_DIM)
        if kind == "int":
            if key == "align":
                return align_label(v), 0
            if key == "golem_hp" and m["sym"] != "S_GOLEM":
                return "%d (inutilisé hors classe golem)" % v, curses.A_DIM
            return str(v), 0
        if kind == "difficulty":
            calc = D.mstrength(m)
            if v is None:
                return "%d (calculée)" % calc, 0
            return "%d (forcée ; calculée : %d)" % (v, calc), \
                self.colors.fg(curses.COLOR_YELLOW)
        if kind == "longtext":
            s = " ".join(v.split())
            return (s or "—"), (0 if s else curses.A_DIM)
        if kind == "plural":
            if v:
                return v, 0
            auto = D.french_plural(m["fr_name"]) if m["fr_name"] else "—"
            doubt = D.plural_doubts(m["fr_name"])
            return "auto : %s%s" % (auto, "  (à vérifier)" if doubt else ""), \
                self.colors.fg(curses.COLOR_YELLOW, True) if doubt \
                else curses.A_DIM
        if not v:
            return "—", curses.A_DIM
        return v, 0

    def draw_form(self, y, x, h, w):
        scr = self.stdscr
        m = self.mon()
        act = self.focus == "form"
        attr = self.colors.fg(curses.COLOR_CYAN, act)
        put(scr, y, x, "┌─ Fiche " + "─" * (w - 10) + "┐", attr)
        for i in range(1, h - 1):
            put(scr, y + i, x, "│", attr)
            put(scr, y + i, x + w - 1, "│", attr)
        put(scr, y + h - 1, x, "└" + "─" * (w - 2) + "┘", attr)
        if not m:
            return
        rows = h - 2
        if self.field < self.form_top + 1:
            self.form_top = max(0, self.field - 1)
        if self.field >= self.form_top + rows:
            self.form_top = self.field - rows + 1
        lw = 20
        for r, f in enumerate(FIELDS[self.form_top:self.form_top + rows]):
            i = self.form_top + r
            yy = y + 1 + r
            if f[0] == "section":
                put(scr, yy, x + 2, "▸ " + f[2],
                    self.colors.fg(curses.COLOR_MAGENTA, True))
                continue
            sel = i == self.field
            la = curses.A_REVERSE if sel and act else \
                (curses.A_BOLD if sel else 0)
            put(scr, yy, x + 2, f[2].ljust(lw), la)
            val, va = self.field_value(m, f)
            put(scr, yy, x + 3 + lw, val, va, w - lw - 5)

    def draw_side(self, y, x, h, w):
        scr = self.stdscr
        m = self.mon()
        attr = self.colors.fg(curses.COLOR_BLUE, True)
        put(scr, y, x, "┌─ Aperçu " + "─" * (w - 11) + "┐", attr)
        for i in range(1, h - 1):
            put(scr, y + i, x, "│", attr)
            put(scr, y + i, x + w - 1, "│", attr)
        put(scr, y + h - 1, x, "└" + "─" * (w - 2) + "┘", attr)
        if not m:
            return
        yy = y + 1
        cw = w - 4
        ch = D.CLASS_CHAR.get(m["sym"], "?")
        put(scr, yy, x + 2, ch, self.colors.mon(m["color"]) | curses.A_BOLD)
        put(scr, yy, x + 4, m["fr_name"] or m["name"], curses.A_BOLD, cw - 2)
        yy += 1
        put(scr, yy, x + 4, "(%s)" % m["name"], curses.A_DIM, cw - 2)
        yy += 2
        hp = ("%d fixes" % m["golem_hp"]) if m["sym"] == "S_GOLEM" else \
            ("1d4" if m["level"] == 0 else "%dd8 (~%d)" % (
                m["level"], m["level"] * 9 // 2))
        lines = [
            ("Difficulté", "%d%s" % (D.difficulty(m), "" if
                                     m["difficulty"] is None else " (forcée)")),
            ("Points de vie", hp),
            ("Dégâts max/tour", str(D.max_damage(m))),
            ("Vitesse", "%d (%s)" % (m["move"], "immobile" if not m["move"]
                                     else "lent" if m["move"] < 9 else
                                     "normal" if m["move"] <= 12 else
                                     "rapide" if m["move"] < 18 else
                                     "très rapide")),
        ]
        st, sa = self.status(m)
        for k, v in lines:
            put(scr, yy, x + 2, k.ljust(16), curses.A_DIM)
            put(scr, yy, x + 18, v, 0, cw - 16)
            yy += 1
        put(scr, yy, x + 2, "Sources".ljust(16), curses.A_DIM)
        put(scr, yy, x + 18, st, sa, cw - 16)
        yy += 2
        # vérification
        res = D.validate(m, self.game(), self.others(m))
        if not res:
            put(scr, yy, x + 2, "✔ aucun problème",
                self.colors.fg(curses.COLOR_GREEN, True))
            return
        for g, msg in res:
            if yy >= y + h - 1:
                break
            a = self.colors.fg(curses.COLOR_RED, True) if g == "erreur" \
                else self.colors.fg(curses.COLOR_YELLOW, True)
            words, line, first = msg.split(), "", True
            for wd in words:
                if len(line) + len(wd) + 1 > cw - 2:
                    put(scr, yy, x + 2, ("✖ " if g == "erreur" else "⚠ ")
                        + line if first else "  " + line, a)
                    yy, line, first = yy + 1, wd, False
                    if yy >= y + h - 1:
                        break
                else:
                    line = (line + " " + wd).strip()
            if yy < y + h - 1 and line:
                put(scr, yy, x + 2, (("✖ " if g == "erreur" else "⚠ ")
                                     if first else "  ") + line, a)
                yy += 1

    # --- édition des champs ------------------------------------------------

    def choices(self, key):
        if key == "fr_gender":
            return [("m", "masculin"), ("f", "féminin")]
        if key == "tile_shape":
            return [(c, "selon la classe" if c == T.SHAPE_AUTO else
                     "tuile dessinée à la main (t)" if c == T.SHAPE_CUSTOM
                     else "") for c in T.shape_choices()]
        if key == "sym":
            return [(s, "%s  %s" % (c, d)) for s, c, d in D.CLASSES
                    if s != "S_WORM_TAIL"]
        if key == "color":
            return [(n, D.COLOR_FR.get(n, "")) for n, _v in D.COLORS]
        if key == "sound":
            return [(n, d) for n, _v, d in D.SOUNDS]
        if key == "size":
            return [(n, d) for n, _v, d in D.SIZES]
        return []

    def move_field(self, delta):
        i = self.field
        while True:
            i += delta
            if i < 0 or i >= len(FIELDS):
                return
            if FIELDS[i][0] != "section":
                self.field = i
                return

    def adjust(self, delta):
        """← → sur le champ courant."""
        m = self.mon()
        f = FIELDS[self.field]
        kind, key = f[0], f[1]
        if kind == "int":
            lo, hi, step = f[4], f[5], f[6]
            v = max(lo, min(hi, m[key] + delta * step))
            if v != m[key]:
                self.checkpoint()
                m[key] = v
        elif kind == "choice":
            ch = [c for c, _ in self.choices(key)]
            i = ch.index(m[key]) if m[key] in ch else 0
            self.checkpoint()
            m[key] = ch[(i + delta) % len(ch)]
        elif kind == "difficulty":
            v = D.mstrength(m) if m[key] is None else m[key]
            self.checkpoint()
            m[key] = max(0, min(255, v + delta))
            if m[key] == D.mstrength(m):
                m[key] = None
        elif kind == "attack":
            a = m["attacks"][key]
            if a[0] == "AT_NONE" and not a[2] and not a[3]:
                return
            self.checkpoint()
            a[2] = max(0, min(255, a[2] + delta))

    def clear_field(self):
        m = self.mon()
        f = FIELDS[self.field]
        if f[0] == "attack":
            self.checkpoint()
            m["attacks"][f[1]] = list(D.NO_ATTK)
            # les attaques suivantes remontent
            used = [a for a in m["attacks"] if a != D.NO_ATTK]
            m["attacks"] = used + [list(D.NO_ATTK)
                                   for _ in range(D.NATTK - len(used))]
        elif f[0] in ("text", "longtext", "plural") \
                and f[1] not in ("name",):
            self.checkpoint()
            m[f[1]] = ""
        elif f[0] == "difficulty":
            self.checkpoint()
            m["difficulty"] = None

    def edit_field(self):
        m = self.mon()
        f = FIELDS[self.field]
        kind, key, label = f[0], f[1], f[2].strip()
        try:
            if kind in ("text", "ident"):
                v = self.input_line(label, m[key], f[3])
                v = v.strip()
                if kind == "ident":
                    v = v.upper()
                    if v.startswith("PM_"):
                        v = v[3:]
                if v == m[key]:
                    return
                self.checkpoint()
                if key == "name" and m["bn"] in (D.derive_bn(m["name"]),
                                                 "NEW_ROBOT"):
                    m["bn"] = D.derive_bn(v)
                m[key] = v
            elif kind == "plural":
                auto = D.french_plural(m["fr_name"])
                v = self.input_line(label, m[key] or auto,
                                    "vide ou inchangé = pluriel calculé "
                                    "(%s)" % auto).strip()
                if v == auto:
                    v = ""
                if v != m[key]:
                    self.checkpoint()
                    m[key] = v
            elif kind == "int":
                v = self.input_int(label, m[key], f[4], f[5], f[3])
                if v != m[key]:
                    self.checkpoint()
                    m[key] = v
            elif kind == "choice":
                ch = self.choices(key)
                cur = [c for c, _ in ch].index(m[key]) \
                    if m[key] in [c for c, _ in ch] else 0
                i = self.menu(label, ch, cur, filterable=len(ch) > 8)
                if ch[i][0] != m[key]:
                    self.checkpoint()
                    m[key] = ch[i][0]
            elif kind == "flags":
                tab = D.FLAG_TABLES[key]
                items = [(n, d) for n, _v, d in tab]
                v = self.checklist(label, items, m[key])
                if v != m[key]:
                    self.checkpoint()
                    m[key] = v
            elif kind == "difficulty":
                s = self.input_line(
                    label, "" if m[key] is None else str(m[key]),
                    "vide = calculée automatiquement (%d)" % D.mstrength(m))
                s = s.strip()
                v = None
                if s:
                    try:
                        v = max(0, min(255, int(s)))
                    except ValueError:
                        return
                if v != m[key]:
                    self.checkpoint()
                    m[key] = v
            elif kind == "attack":
                self.edit_attack(m, key)
            elif kind == "longtext":
                v = self.text_area(label, m[key])
                if v != m[key]:
                    self.checkpoint()
                    m[key] = v
        except Cancel:
            pass

    def edit_attack(self, m, i):
        a = m["attacks"][i]
        ats = [(n, d) for n, _v, d in D.ATTACK_TYPES]
        cur = [n for n, _ in ats].index(a[0]) if a[0] in D.AT_VALUE else 0
        k = self.menu("Attaque %d : type" % (i + 1), ats, cur)
        at = ats[k][0]
        # les dégâts que le jeu ne gère pas avec ce type sont signalés
        ads = [(n, d if D.attack_allows(at, n) else "✖ " + d +
                " (sans effet avec ce type)")
               for n, _v, d in D.DAMAGE_TYPES]
        names = [n for n, _ in ads]
        cur = names.index(a[1]) if a[1] in D.AD_VALUE and \
            D.attack_allows(at, a[1]) else \
            next(i for i, n in enumerate(names) if D.attack_allows(at, n))
        k = self.menu("Attaque %d : dégâts (%s)" % (i + 1, D.AT_DESC[at]),
                      ads, cur)
        ad = ads[k][0]
        dice = "%dd%d" % (a[2] or 1, a[3] or 6)
        while True:
            s = self.input_line("Attaque %d : dés" % (i + 1), dice,
                                "NdM : N dés à M faces (2d6) ; 0d0 pour "
                                "un effet sans dégâts")
            mo = re.match(r"^\s*(\d+)\s*[dD]\s*(\d+)\s*$", s)
            if mo and int(mo.group(1)) < 256 and int(mo.group(2)) < 256:
                break
        self.checkpoint()
        m["attacks"][i] = [at, ad, int(mo.group(1)), int(mo.group(2))]

    def edit_tile(self):
        m = self.mon()
        if not m:
            return
        if not self.confirm(
                "La tuile n'apparaît que dans les versions graphiques\n"
                "(Qt, X11), pas dans le terminal. La dessiner quand même ?",
                "Tuile"):
            return
        old = T.tile_for(m)
        new = self.tile_editor(old, m["fr_name"] or m["name"])
        if new != old:
            self.checkpoint()
            m["tile"] = new
            m["tile_shape"] = T.SHAPE_CUSTOM

    # --- monstres -----------------------------------------------------------

    def unique_names(self, m):
        """Rend le nom et l'identifiant uniques (suffixe mk II, mk III)."""
        taken = {o["name"] for o in self.game() + self.monsters}
        bns = {o["bn"] for o in self.game() + self.monsters}
        base, bbn, n = m["name"], m["bn"], 1
        frbase = m["fr_name"]
        roman = ["", " mk II", " mk III", " mk IV", " mk V", " mk VI"]
        while m["name"] in taken or m["bn"] in bns:
            n += 1
            suf = roman[n - 1] if n <= len(roman) else " mk %d" % n
            m["name"] = base + suf
            m["bn"] = bbn + "_MK%d" % n
            if frbase:
                m["fr_name"] = frbase + suf
        return m

    def add_monster(self, m):
        self.checkpoint()
        self.monsters.insert(self.cur + 1 if self.monsters else 0, m)
        self.cur = self.cur + 1 if len(self.monsters) > 1 else 0
        self.focus = "form"
        self.field = 1

    def new_monster(self):
        try:
            i = self.menu("Nouveau monstre : modèle",
                          T.template_list())
            m = T.from_template(i)
            fr = self.input_line("Nom français", m["fr_name"],
                                 "nom affiché dans le jeu")
            en = self.input_line("Nom anglais (interne)", m["name"],
                                 "en minuscules ; à taper avec ^G en "
                                 "mode wizard")
        except Cancel:
            return
        m["fr_name"] = fr.strip() or m["fr_name"]
        if en.strip() and en.strip() != m["name"]:
            m["name"] = en.strip()
            m["bn"] = D.derive_bn(m["name"])
        self.add_monster(self.unique_names(m))
        self.msg = "Monstre créé : %s" % (m["fr_name"] or m["name"])

    def duplicate(self):
        m = self.mon()
        if not m:
            return
        self.add_monster(self.unique_names(copy.deepcopy(m)))
        self.msg = "Copie créée : %s" % self.mon()["name"]

    def import_game(self):
        game = self.game()
        if not game:
            self.msg = "Monstres du jeu introuvables dans %s" % self.src
            return
        fr = self.fr_names()
        items = [("%s %s" % (D.CLASS_CHAR.get(g["sym"], "?"),
                             fr.get(g["name"], (g["name"],))[0]),
                  "%s, niv %d, diff %d" % (g["name"], g["level"],
                                           g["difficulty"]))
                 for g in game]
        try:
            i = self.menu("Importer un monstre du jeu (%d)" % len(game),
                          items)
        except Cancel:
            return
        m = D.normalize(copy.deepcopy(game[i]))
        m["fr_name"], m["fr_gender"] = fr.get(m["name"], ("", "m"))
        for k in ("name_m", "name_f"):
            if m[k]:
                m["fr_" + k] = fr.get(m[k], ("",))[0]
        hp = D.read_golemhp(os.path.join(self.src, I.MAKEMON_C))
        m["golem_hp"] = hp.get(m["bn"], m["golem_hp"])
        if m["difficulty"] == D.mstrength(m):
            m["difficulty"] = None
        tile = self.game_tile(m["name"])
        if tile:
            m["tile"], m["tile_shape"] = tile, T.SHAPE_CUSTOM
        self.add_monster(self.unique_names(m))
        self.msg = "Importé : %s — renommez-le à votre goût" % m["name"]

    def game_tile(self, name):
        path = os.path.join(self.src, I.TILES)
        try:
            with open(path, encoding="utf-8") as f:
                text = f.read()
        except OSError:
            return None
        mo = re.search(r"^# tile \d+ \(%s,male\)\n\{\n(.*?)^\}" %
                       re.escape(name), text, re.M | re.S)
        if not mo:
            return None
        rows = [r.strip() for r in mo.group(1).split("\n") if r.strip()]
        return rows if len(rows) == D.TILE_SIZE else None

    def delete(self):
        m = self.mon()
        if not m:
            return
        if not self.confirm("Supprimer « %s » du projet ?\n(il reste dans "
                            "les sources tant que vous n'intégrez pas à "
                            "nouveau)" % (m["fr_name"] or m["name"])):
            return
        self.checkpoint()
        del self.monsters[self.cur]
        self.cur = max(0, min(self.cur, len(self.monsters) - 1))
        self.msg = "Supprimé"

    def move_monster(self, delta):
        j = self.cur + delta
        if not self.monsters or not 0 <= j < len(self.monsters):
            return
        self.checkpoint()
        ms = self.monsters
        ms[self.cur], ms[j] = ms[j], ms[self.cur]
        self.cur = j

    # --- vues -----------------------------------------------------------------

    def show_code(self):
        m = self.mon()
        if not m:
            return
        lines = ["/* include/monsters.h, à la fin de la classe %s */" %
                 m["sym"], ""]
        lines += [(l, self.cyan()) for l in D.c_entry(m).split("\n")]
        if m["sym"] == "S_GOLEM":
            lines += ["", "/* src/makemon.c, golemhp() */",
                      ("    case PM_%s:" % m["bn"], self.cyan()),
                      ("        return %d;" % m["golem_hp"], self.cyan())]
        lines += ["", "# po/themes/fr@cyber.po"]
        lines += [(l, self.cyan()) for e in I.po_entries(m, "cyber")
                  for l in e.split("\n")[1:] + [""]]
        blk = I.data_block(m, "encyclo_fr")
        if blk:
            lines += ["# dat/data-fr@cyber.base"]
            lines += [(l, self.cyan()) for l in blk.split("\n")[1:-2]]
        self.viewer("Code de %s" % m["name"], lines)

    def show_validation(self):
        lines = []
        nerr = 0
        for m in self.monsters:
            res = D.validate(m, self.game(), self.others(m))
            nerr += sum(g == "erreur" for g, _ in res)
            head = "%s %s (%s)" % (D.CLASS_CHAR.get(m["sym"], "?"),
                                   m["fr_name"] or m["name"], m["name"])
            lines.append((head, curses.A_BOLD))
            if not res:
                lines.append(("   ✔ aucun problème",
                              self.colors.fg(curses.COLOR_GREEN, True)))
            for g, msg in res:
                lines.append(("   %s %s" % ("✖" if g == "erreur" else "⚠",
                                            msg),
                              self.colors.fg(curses.COLOR_RED, True)
                              if g == "erreur" else
                              self.colors.fg(curses.COLOR_YELLOW, True)))
            lines.append("")
        if not self.monsters:
            lines = ["Aucun monstre dans le projet."]
        self.viewer("Vérification : %d erreur(s)" % nerr, lines)
        return nerr

    def show_compare(self):
        m = self.mon()
        if not m:
            return
        d = D.difficulty(m)
        fr = self.fr_names()
        near = sorted(self.game(), key=lambda g: (abs(g["difficulty"] - d),
                                                  g["level"]))[:30]
        lines = [("Monstres du jeu de difficulté proche de %d :" % d,
                  curses.A_BOLD), "",
                 "    nom                         niv  vit  CA  diff  "
                 "dégâts max", ""]
        for g in sorted(near, key=lambda g: g["difficulty"]):
            name = fr.get(g["name"], (g["name"],))[0]
            lines.append((" %s  %-27s %3d  %3d %3d  %4d  %5d" % (
                D.CLASS_CHAR.get(g["sym"], "?"), name[:27], g["level"],
                g["move"], g["ac"], g["difficulty"], D.max_damage(g)),
                self.colors.mon(g["color"])))
        lines += ["", (" ▶ %-28s %3d  %3d %3d  %4d  %5d" % (
            (m["fr_name"] or m["name"])[:28], m["level"], m["move"],
            m["ac"], d, D.max_damage(m)), curses.A_BOLD)]
        self.viewer("Comparaison", lines)

    def help(self):
        self.viewer("Aide", HELP)

    # --- sources -------------------------------------------------------------

    def check_src(self):
        err = I.check_tree(self.src)
        if err:
            self.message_box("Sources introuvables", [
                err, "", "Indiquez le dossier des sources avec --src ou "
                "la variable NHMONEDIT_SRC."])
            return False
        return True

    def integrate(self):
        if not self.check_src():
            return
        if not self.monsters:
            self.msg = "Aucun monstre à intégrer (R pour retirer)"
            return
        errs = []
        for m in self.monsters:
            for g, msg in D.validate(m, self.game(), self.others(m)):
                if g == "erreur":
                    errs.append("%s : %s" % (m["name"], msg))
        if errs:
            self.viewer("Intégration impossible : corrigez d'abord",
                        errs)
            return
        try:
            files = I.plan(self.src, self.monsters)
        except I.InstallError as e:
            self.message_box("Intégration impossible", [str(e)])
            return
        diff = I.diff(self.src, files)
        if not diff:
            self.msg = "Les sources sont déjà à jour"
            return
        lines = []
        for l in diff.split("\n"):
            a = self.colors.fg(curses.COLOR_GREEN) if l.startswith("+") \
                else self.colors.fg(curses.COLOR_RED) if l.startswith("-") \
                else self.cyan() if l.startswith("@@") else 0
            lines.append((l, a))
        self.viewer("Aperçu des changements (q pour continuer)", lines)
        changed = [r for r, t in files.items()
                   if open(os.path.join(self.src, r),
                           encoding="utf-8").read() != t]
        if not self.confirm("Écrire dans les sources (%s) ?\n\n%s\n\n"
                            "Une copie des fichiers va dans sauvegardes/."
                            "\nSi la liste des monstres change, EDITLEVEL "
                            "augmente :\nles anciennes sauvegardes ne se "
                            "chargeront plus." % (
                                self.src, "\n".join("  " + c
                                                    for c in changed))):
            return
        ch, lvl, bk = I.apply(self.src, files, True, BACKUP_DIR)
        self._game = None
        self._inst = (None, {})
        if self.modified:
            self.save()
        self.msg = "Intégré : %d fichier(s)%s — m pour compiler" % (
            len(ch), ", EDITLEVEL %d" % lvl if lvl is not None else "")

    def remove(self):
        if not self.check_src():
            return
        ids = I.installed_ids(self.src)
        if not ids:
            self.msg = "Aucun monstre de l'éditeur dans les sources"
            return
        if not self.confirm("Retirer des sources les %d monstres ajoutés "
                            "par l'éditeur ?\n%s" % (len(ids), ", ".join(
                                ids))):
            return
        ch, lvl, bk = I.uninstall(self.src, True, BACKUP_DIR)
        self._game = None
        self._inst = (None, {})
        self.msg = "Retiré de %d fichier(s)" % len(ch)

    def run_external(self, title, cmd, cwd):
        """Lance une commande hors de curses, la sortie dans le terminal."""
        curses.def_prog_mode()
        curses.endwin()
        print("\033[1;35m== nhmonedit : %s ==\033[0m" % title)
        print("$ cd %s && %s\n" % (shlex.quote(cwd), cmd))
        t = time.time()
        try:
            rc = subprocess.call(cmd, shell=True, cwd=cwd)
        except KeyboardInterrupt:
            rc = -1
        color = "32" if rc == 0 else "31"
        print("\n\033[1;%sm== terminé (code %d, %.0f s) ==\033[0m"
              % (color, rc, time.time() - t))
        try:
            input("Entrée pour revenir à l'éditeur… ")
        except (EOFError, KeyboardInterrupt):
            pass
        curses.reset_prog_mode()
        self.stdscr.clear()
        curses.curs_set(0)
        return rc

    def make(self):
        if not self.check_src():
            return
        if not os.path.isfile(os.path.join(self.src, "Makefile")):
            self.message_box("Sources non configurées", [
                "Pas de Makefile : configurez d'abord les sources :",
                "  cd sys/unix && sh setup.sh hints/linux.500"])
            return
        jobs = os.cpu_count() or 2
        rc = self.run_external("compilation", "make -j%d" % jobs, self.src)
        self.msg = "Compilation réussie — U pour mettre à jour le jeu" \
            if rc == 0 else "La compilation a échoué (code %d)" % rc

    def make_update(self):
        if not self.check_src():
            return
        if not self.confirm(
                "Mettre à jour le jeu installé (make update) ?\n\n"
                "sysconf, scores et dossier save sont conservés ;\n"
                "le jeu précédent est gardé en nethack.old."):
            return
        rc = self.run_external("mise à jour du jeu", "make update",
                               self.src)
        self.msg = "Jeu mis à jour — j pour l'essayer" if rc == 0 \
            else "make update a échoué (code %d)" % rc

    def hackdir(self):
        for d in HACKDIRS:
            if d and os.access(os.path.join(d, "nethack"), os.X_OK):
                return d
        return None

    def play(self):
        d = self.hackdir()
        if not d:
            self.message_box("Jeu introuvable", [
                "Pas d'exécutable nethack installé. Compilez (m) puis",
                "mettez à jour le jeu (U), ou indiquez son dossier avec",
                "NHMONEDIT_HACKDIR."])
            return
        exe = os.path.join(d, "nethack")
        newer = [p for p in (I.MONSTERS_H,)
                 if os.path.isfile(os.path.join(self.src, p)) and
                 os.path.getmtime(os.path.join(self.src, p)) >
                 os.path.getmtime(exe)]
        names = [m["name"] for m in self.monsters]
        lines = ["Mode wizard : Ctrl-G (créer un monstre), puis tapez le",
                 "nom ANGLAIS du monstre. « ; » pour le regarder.", ""]
        if names:
            lines += ["Vos monstres : " + ", ".join(names[:6]) +
                      ("…" if len(names) > 6 else ""), ""]
        if newer:
            lines += ["⚠ Le jeu installé est plus ancien que monsters.h :",
                      "  compilez (m) et mettez à jour (U) d'abord.", ""]
        lines += ["Lancer le jeu maintenant ?"]
        if not self.confirm("\n".join(lines), "Essayer en jeu"):
            return
        cmd = "HACKDIR=%s %s -D" % (shlex.quote(d), shlex.quote(exe))
        self.run_external("NetHack (mode wizard)", cmd, d)

    # --- boucle -------------------------------------------------------------

    def quit(self):
        if not self.modified:
            return True
        try:
            i = self.menu("Projet modifié", [
                ("Enregistrer et quitter", ""),
                ("Quitter sans enregistrer", ""),
                ("Annuler", "")], filterable=False)
        except Cancel:
            return False
        if i == 0:
            self.save()
            return True
        return i == 1

    def run(self):
        curses.curs_set(0)
        self.stdscr.keypad(True)
        while True:
            self.draw()
            k = get_key(self.stdscr)
            if k != curses.KEY_RESIZE:
                self.msg = ""
            if k == curses.KEY_RESIZE:
                continue
            if k == "q":
                if self.quit():
                    return
            elif k == "?":
                self.help()
            elif k == "s":
                self.save()
            elif k == "u":
                self.undo()
            elif k == "n":
                self.new_monster()
            elif k == "d":
                self.duplicate()
            elif k == "i":
                self.import_game()
            elif k == "t":
                self.edit_tile()
            elif k == "v":
                self.show_validation()
            elif k == "c":
                self.show_code()
            elif k == "b":
                self.show_compare()
            elif k == "I":
                self.integrate()
            elif k == "R":
                self.remove()
            elif k == "m":
                self.make()
            elif k == "U":
                self.make_update()
            elif k == "j":
                self.play()
            elif k == "\t":
                if self.monsters:
                    self.focus = "form" if self.focus == "list" else "list"
            elif self.focus == "list":
                self.key_list(k)
            else:
                self.key_form(k)

    def key_list(self, k):
        n = len(self.monsters)
        if not n:
            return
        if k == curses.KEY_UP:
            self.cur = max(0, self.cur - 1)
        elif k == curses.KEY_DOWN:
            self.cur = min(n - 1, self.cur + 1)
        elif k == curses.KEY_PPAGE:
            self.cur = max(0, self.cur - 10)
        elif k == curses.KEY_NPAGE:
            self.cur = min(n - 1, self.cur + 10)
        elif k == curses.KEY_HOME:
            self.cur = 0
        elif k == curses.KEY_END:
            self.cur = n - 1
        elif is_enter(k) or k == curses.KEY_RIGHT:
            self.focus = "form"
        elif k in (curses.KEY_DC, "X"):
            self.delete()
        elif k == "<":
            self.move_monster(-1)
        elif k == ">":
            self.move_monster(1)

    def key_form(self, k):
        if not self.monsters:
            return
        if k == curses.KEY_UP:
            self.move_field(-1)
        elif k == curses.KEY_DOWN:
            self.move_field(1)
        elif k == curses.KEY_PPAGE:
            for _ in range(10):
                self.move_field(-1)
        elif k == curses.KEY_NPAGE:
            for _ in range(10):
                self.move_field(1)
        elif k == curses.KEY_HOME:
            self.field = 1
        elif k == curses.KEY_END:
            self.field = len(FIELDS) - 1
        elif k == curses.KEY_LEFT:
            self.adjust(-1)
        elif k == curses.KEY_RIGHT:
            self.adjust(1)
        elif k in ("+", "="):
            self.adjust(1)
        elif k == "-":
            self.adjust(-1)
        elif is_enter(k) or k == " ":
            self.edit_field()
        elif k in (curses.KEY_DC, curses.KEY_BACKSPACE, "\x7f"):
            self.clear_field()
        elif k == ESC:
            self.focus = "list"


def parse_args(argv):
    project, src = DEFAULT_PROJECT, os.environ.get("NHMONEDIT_SRC",
                                                    DEFAULT_SRC)
    args = list(argv)
    while args:
        a = args.pop(0)
        if a in ("-h", "--help"):
            print(__doc__.strip())
            sys.exit(0)
        elif a == "--src" and args:
            src = args.pop(0)
        elif a.startswith("--src="):
            src = a.split("=", 1)[1]
        elif a.startswith("-"):
            sys.exit("Option inconnue : %s (voir --help)" % a)
        else:
            project = a
    return os.path.abspath(project), os.path.abspath(src)


def main(argv=None):
    project, src = parse_args(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("ESCDELAY", "25")
    import locale
    locale.setlocale(locale.LC_ALL, "")
    curses.wrapper(lambda scr: Editor(scr, project, src).run())


if __name__ == "__main__":
    main()
