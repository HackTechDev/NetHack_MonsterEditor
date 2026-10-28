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

import nhmon_config as C
import nhmon_data as D
from nhmon_i18n import LANG, _
import nhmon_install as I
from nhmon_game import Game
import nhmon_project as P
import nhmon_templates as T
from nhmon_ui import (Cancel, Colors, ESC, Mouse, Popups, clip,
                      enable_mouse, get_key, is_enter, put, wheel)

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PROJECT = os.path.join(HERE, "monstres.json")
DEFAULT_SRC = os.path.normpath(os.path.join(HERE, "..", "NetHack-5.0.0"))
BACKUP_DIR = os.path.join(HERE, "sauvegardes")

ALIGN_HINT = _("négatif : chaotique, 0 : neutre, positif : loyal ; " \
             "-128 : sans alignement (A_NONE)")

# (type, clé, libellé, aide[, min, max, pas])
FIELDS = [
    ("section", None, _("Identité"), ""),
    ("text", "fr_name", _("Nom français"), _("nom affiché dans le jeu "
     "(thème fr@cyber)")),
    ("choice", "fr_gender", _("Genre (français)"), _("accord des phrases : "
     "« le », « la », « détruit », « détruite »")),
    ("plural", "fr_plural", _("Pluriel français"), _("« trois mechas de "
     "combat » : vide = calculé par le jeu (s ou x à chaque mot avant "
     "« de », « à »…) ; Entrée pour le corriger")),
    ("text", "name", _("Nom anglais"), _("nom interne du jeu (en "
     "minuscules) ; c'est lui qu'on tape avec ^G en mode wizard")),
    ("ident", "bn", _("Identifiant PM_"), _("nom C : PM_<identifiant>, en "
     "majuscules")),
    ("text", "name_m", _("  nom anglais masc."), _("facultatif : nom "
     "propre au masculin (sinon le nom anglais sert pour tous)")),
    ("text", "name_f", _("  nom anglais fém."), _("facultatif : nom propre au "
     "féminin")),
    ("text", "fr_name_m", _("  nom français masc."), _("traduction du nom "
     "masculin")),
    ("text", "fr_name_f", _("  nom français fém."), _("traduction du nom "
     "féminin")),
    ("choice", "sym", _("Classe"), _("lettre affichée sur la carte ; la "
     "classe golem (') donne des PV fixes, comme il sied à un robot")),
    ("choice", "color", _("Couleur"), _("couleur de la lettre sur la carte")),
    ("after", "after", _("Placer après"), _("rang dans monsters.h : après "
     "quel monstre du jeu de la même classe ; vide = fin de la classe "
     "(l'ordre compte pour les monstres créés « de la même classe »)")),
    ("section", None, _("Caractéristiques"), ""),
    ("int", "level", _("Niveau"), _("niveau de base (0 à 49) : PV, toucher, "
     "profondeur d'apparition"), 0, 49, 1),
    ("int", "move", _("Vitesse"), _("12 = humain, 0 = immobile (tourelle), "
     "20+ = très rapide"), 0, 127, 1),
    ("int", "ac", _("Classe d'armure"), _("10 = sans armure, 0 = blindé, "
     "négatif = très blindé"), -128, 127, 1),
    ("int", "mr", _("Résist. magie %"), _("chance de résister aux sorts et "
     "baguettes (0 à 100)"), 0, 127, 5),
    ("int", "align", _("Alignement"), ALIGN_HINT, -128, 127, 1),
    ("int", "golem_hp", _("PV fixes (golem)"), _("seulement pour la classe "
     "golem (') : points de vie fixes (golem de fer : 120)"), 1, 999, 5),
    ("difficulty", "difficulty", _("Difficulté"), _("calculée comme le jeu "
     "(mstrength) ; Entrée pour forcer une valeur, vide = automatique")),
    ("section", None, _("Génération"), ""),
    ("int", "freq", _("Fréquence"), _("0 = jamais au hasard … 7 = très "
     "courant (la plupart : 1 à 3)"), 0, 7, 1),
    ("flags", "geno", _("Drapeaux G_"), _("unique, groupes, génocide, "
     "cadavre…")),
    ("section", None, _("Attaques"), ""),
] + [("attack", i, _("Attaque %d") % (i + 1), _("Entrée : type, dégâts, dés ; "
      "Suppr : vider ; ←→ : changer le nombre de dés"))
     for i in range(D.NATTK)] + [
    ("section", None, _("Corps"), ""),
    ("int", "weight", _("Poids"), _("humain : 1450, golem de fer : 2000"),
     0, 65535, 50),
    ("int", "nutrition", _("Nutrition"), _("valeur nutritive du cadavre "
     "(0 pour une épave de robot)"), 0, 65535, 50),
    ("choice", "sound", _("Son"), _("bruit ou phrases du monstre (#parler)")),
    ("choice", "size", _("Taille"), _("taille physique")),
    ("flags", "mr1", _("Résistances"), _("résistances du monstre")),
    ("flags", "mr2", _("Conférées"), _("résistances données en mangeant le "
     "cadavre")),
    ("flags", "flags1", _("Drapeaux M1"), _("corps et déplacement")),
    ("flags", "flags2", _("Drapeaux M2"), _("nature et comportement")),
    ("flags", "flags3", _("Drapeaux M3"), _("divers (infravision, attente…)")),
    ("section", None, _("Apparence et textes"), ""),
    ("choice", "tile_shape", _("Silhouette (tuile)"), _("image des versions "
     "graphiques (Qt, X11) seulement, invisible dans le terminal ; "
     "colorée d'après la couleur du monstre")),
    ("longtext", "encyclo_fr", _("Encyclopédie (fr)"), _("texte de « ; » et "
     "« / » dans le jeu, en français")),
    ("longtext", "encyclo_en", _("Encyclopédie (en)"), _("même texte en "
     "anglais (sinon le texte français est repris)")),
    ("longtext", "notes", _("Notes"), _("vos notes (non intégrées au jeu)")),
]

HELP = [
    _("nhmonedit — éditeur de monstres pour NetHack 5.0 cyberpunk"),
    "",
    _("Deux zones : la liste des monstres du projet (à gauche) et la fiche"),
    _("du monstre choisi. Tab passe de l'une à l'autre."),
    "",
    _("Dans la fiche :"),
    _("  ↑ ↓          champ précédent / suivant"),
    _("  ← →          changer une valeur (nombre, choix, dés d'attaque)"),
    _("  Entrée       modifier le champ"),
    _("  Suppr        vider (attaque, texte)"),
    "",
    _("Monstres :"),
    _("  n            nouveau monstre d'après un modèle (robots, mechas…)"),
    _("  d            dupliquer le monstre"),
    _("  i            importer un monstre du jeu comme base"),
    _("  Suppr / X    supprimer le monstre (dans la liste)"),
    _("  < >          déplacer le monstre dans la liste"),
    _("  /            aller à un monstre (tapez une partie de son nom)"),
    _("  t            dessiner la tuile à la main (versions graphiques"),
    _("               seulement ; sinon la silhouette suffit)"),
    "",
    _("Contrôle :"),
    _("  v            vérifier tous les monstres"),
    _("  c            voir le code C (entrée MON() de monsters.h)"),
    _("  b            comparer aux monstres du jeu (difficulté proche)"),
    _("  B            fiche comparée : deux monstres côte à côte (un"),
    _("               autre du projet ou du jeu), différences en jaune"),
    "",
    _("Sources du jeu :"),
    _("  I            intégrer les monstres aux sources (aperçu, puis"),
    _("               confirmation ; copie des fichiers dans sauvegardes/)"),
    _("  R            retirer les monstres des sources, ou rétablir"),
    _("               une sauvegarde (annuler une intégration)"),
    _("  m            compiler (make)"),
    _("  U            mettre à jour le jeu installé (make update : garde"),
    _("               sysconf, scores et sauvegardes)"),
    _("  j            essayer en jeu : NetHack en mode wizard à côté de"),
    _("               l'éditeur (tmux), le monstre y est créé ; dans"),
    _("               une partie en cours, j en crée un autre"),
    "",
    _("Projet :"),
    _("  p            menu du projet : fusionner un autre projet,"),
    _("               exporter ou importer un monstre, enregistrer le"),
    _("               monstre comme modèle personnel…"),
    "",
    _("Général :"),
    _("  s            enregistrer le projet"),
    _("  u            annuler la dernière modification"),
    _("  Ctrl-R       rétablir ce qui a été annulé (aussi Ctrl-Y)"),
    "",
    _("Souris : un clic choisit un monstre ou un champ, un double clic"),
    _("ouvre la fiche ou modifie le champ ; la molette fait défiler. Dans"),
    _("les menus, un second clic valide. Pour sélectionner du texte dans"),
    _("le terminal, maintenez Maj (NHMONEDIT_MOUSE=0 coupe la souris)."),
    _("  ?            cette aide       q  quitter"),
    "",
    _("En jeu (mode wizard) : Ctrl-G puis le nom ANGLAIS du monstre pour"),
    _("le créer à côté de vous ; « ; » pour le regarder (encyclopédie)."),
    "",
    _("Les nouveaux monstres changent la liste mons[] : l'intégration"),
    _("augmente EDITLEVEL (include/patchlevel.h), les anciennes sauvegardes"),
    _("et fichiers de bones ne se chargent plus."),
]


def align_label(v):
    if v == D.ALIGN_NONE:
        return _("A_NONE (sans alignement)")
    if v < 0:
        return _("%d (chaotique)") % v
    if v > 0:
        return _("%d (loyal)") % v
    return _("0 (neutre)")


def frame_top(title, w):
    """« ┌─ Titre ────┐ » sur w colonnes."""
    head = "┌─ %s " % title
    return head + "─" * max(0, w - len(head) - 1) + "┐"


def hp_text(m):
    """Points de vie à la création (makemon.c)."""
    if m["sym"] == "S_GOLEM":
        return _("%d fixes") % m["golem_hp"]
    if m["level"] == 0:
        return "1d4"
    return "%dd8 (~%d)" % (m["level"], m["level"] * 9 // 2)


def num(v):
    """4.5 -> « 4,5 » (« 4.5 » en anglais), 4.0 -> « 4 »."""
    s = ("%.1f" % v).rstrip("0").rstrip(".")
    return s if LANG == "en" else s.replace(".", ",")


def attack_hint(m, attack):
    """Ligne d'aide d'une attaque : dégâts moyens et message du jeu."""
    if attack not in D.attacks_used(m):
        return None
    avg, msg, note = D.attack_preview(m, attack)
    return _("moy. %s pts — « %s »%s") % (num(avg), msg,
                                       " (%s)" % note if note else "")


def short_flags(names):
    return ", ".join(n.split("_", 1)[1] for n in names) if names else "—"


class Editor(Popups, Game):
    def __init__(self, stdscr, project, src, config=None, config_errs=()):
        self.stdscr = stdscr
        self.config = config or {}
        self.colors = Colors()
        self.project = project
        self.src = src
        self.monsters = []
        self.cur = 0
        self.field = 1
        self.focus = "list"
        self.modified = False
        self.undo_stack = []
        self.redo_stack = []
        self.autosave_delay = self.config.get("autosave", P.AUTOSAVE_DELAY)
        self.autosave_time = time.time()
        self.msg = ""
        self.form_top = 0
        self.list_top = 0
        self.areas = {}         # zone -> (y, x, h, w), pour la souris
        self._game = None
        self._fr = None
        self._inst = (None, {})
        self.load()
        if config_errs:
            self.msg = _("Configuration : %s") % "; ".join(config_errs)

    # --- données ----------------------------------------------------------

    def load(self):
        if os.path.isfile(self.project):
            with open(self.project, encoding="utf-8") as f:
                data = json.load(f)
            self.monsters = [D.normalize(m) for m in data.get("monsters", [])]
            self.msg = _("Projet ouvert : %s (%d monstres)") % (
                self.project, len(self.monsters))
        else:
            self.monsters = []
            self.msg = _("Nouveau projet : %s — « n » pour créer un " \
                       "monstre") % self.project

    def save(self):
        P.write_project(self.project, self.monsters)
        P.drop_autosave(self.project)
        self.modified = False
        self.msg = _("Enregistré : %s") % self.project

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
            return _("non intégré"), curses.A_DIM
        if inst[m["bn"]] == D.c_entry(m, marker=False):
            return _("intégré"), self.colors.fg(curses.COLOR_GREEN, True)
        return _("intégré, modifié depuis"), \
            self.colors.fg(curses.COLOR_YELLOW, True)

    def mon(self):
        return self.monsters[self.cur] if self.monsters else None

    def others(self, m):
        return [o for o in self.monsters if o is not m]

    def checkpoint(self):
        self.undo_stack.append((copy.deepcopy(self.monsters), self.cur))
        del self.undo_stack[:-100]
        self.redo_stack = []
        self.modified = True

    def undo(self, redo=False):
        """u annule, Ctrl-R rétablit ce qui vient d'être annulé."""
        src, dst = (self.redo_stack, self.undo_stack) if redo else \
            (self.undo_stack, self.redo_stack)
        if not src:
            self.msg = _("Rien à rétablir") if redo else _("Rien à annuler")
            return
        dst.append((self.monsters, self.cur))
        self.monsters, self.cur = src.pop()
        self.cur = min(self.cur, max(0, len(self.monsters) - 1))
        self.modified = True
        self.msg = _("Rétabli") if redo else _("Annulé")

    # --- dessin -----------------------------------------------------------

    def redraw(self):
        self.draw()

    def draw(self):
        scr = self.stdscr
        scr.erase()
        H, W = scr.getmaxyx()
        if H < 20 or W < 70:
            put(scr, 0, 0, _("Terminal trop petit (70x20 minimum)"))
            scr.refresh()
            return
        title = _(" nhmonedit ▸ robots & mechas de Night City ")
        proj = " %s%s " % (os.path.basename(self.project),
                           _(" [modifié]") if self.modified else "")
        bar = self.colors.pair(curses.COLOR_BLACK, curses.COLOR_MAGENTA)
        put(scr, 0, 0, " " * W, bar)
        put(scr, 0, 0, title, bar | curses.A_BOLD)
        put(scr, 0, W - len(proj) - 1, proj, bar)
        lw = 30
        rw = 40 if W >= 120 else 0
        fw = W - lw - rw
        self.areas = {"list": (1, 0, H - 3, lw), "form": (1, lw, H - 3, fw)}
        self.draw_list(1, 0, H - 3, lw)
        self.draw_form(1, lw, H - 3, fw)
        if rw:
            self.draw_side(1, lw + fw, H - 3, rw)
        # aide du champ et message
        m = self.mon()
        hint = ""
        if self.focus == "form" and m:
            f = FIELDS[self.field]
            hint = (f[0] == "attack" and attack_hint(m, m["attacks"][f[1]])) \
                or f[3]
        put(scr, H - 2, 0, (" " + hint).ljust(W),
            self.colors.fg(curses.COLOR_CYAN))
        keys = _(" n:nouveau d:dupl. i:importer v:vérif c:code b:comparer " \
               "I:intégrer m:make U:update j:jouer s:enreg. ?:aide q:quitter")
        put(scr, H - 1, 0, (" " + self.msg).ljust(W) if self.msg else
            keys.ljust(W), self.colors.pair(curses.COLOR_BLACK,
                                            curses.COLOR_CYAN))
        scr.refresh()

    def draw_list(self, y, x, h, w):
        scr = self.stdscr
        act = self.focus == "list"
        attr = self.colors.fg(curses.COLOR_MAGENTA, act)
        put(scr, y, x, frame_top(_("Monstres"), w), attr)
        for i in range(1, h - 1):
            put(scr, y + i, x, "│", attr)
            put(scr, y + i, x + w - 1, "│", attr)
        put(scr, y + h - 1, x, "└" + "─" * (w - 2) + "┘", attr)
        if not self.monsters:
            put(scr, y + 2, x + 2, _("(vide)"), curses.A_DIM)
            put(scr, y + 3, x + 2, _("n : nouveau monstre"), curses.A_DIM)
            put(scr, y + 4, x + 2, _("i : importer du jeu"), curses.A_DIM)
            return
        rows = h - 2
        top = max(0, min(self.cur - rows // 2, len(self.monsters) - rows))
        self.list_top = top
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
            mark = "✖" if errs else (
                "●" if st == _("intégré") else
                "◐" if st.startswith(_("intégré")) else "")
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
                return {"m": _("masculin"), "f": _("féminin")}.get(v, v), 0
            if key == "tile_shape":
                if v == T.SHAPE_AUTO:
                    return _("auto (%s, d'après la classe)") % \
                        T.shape_label(T.shape_of(m)), 0
                if v == T.SHAPE_CUSTOM:
                    return _("personnalisée (dessinée avec t)"), 0
                return T.shape_label(v), 0
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
                return _("%d (inutilisé hors classe golem)") % v, curses.A_DIM
            return str(v), 0
        if kind == "difficulty":
            calc = D.mstrength(m)
            if v is None:
                return _("%d (calculée)") % calc, 0
            return _("%d (forcée ; calculée : %d)") % (v, calc), \
                self.colors.fg(curses.COLOR_YELLOW)
        if kind == "longtext":
            s = " ".join(v.split())
            return (s or "—"), (0 if s else curses.A_DIM)
        if kind == "after":
            if not v:
                return _("fin de la classe"), curses.A_DIM
            fr = self.fr_names().get(v, ("",))[0]
            return "%s%s" % (v, " (%s)" % fr if fr else ""), 0
        if kind == "plural":
            if v:
                return v, 0
            auto = D.french_plural(m["fr_name"]) if m["fr_name"] else "—"
            doubt = D.plural_doubts(m["fr_name"])
            return _("auto : %s%s") % (
                auto, _("  (à vérifier)") if doubt else ""), \
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
        put(scr, y, x, frame_top(_("Fiche"), w), attr)
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
        put(scr, y, x, frame_top(_("Aperçu"), w), attr)
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
        hp = hp_text(m)
        lines = [
            (_("Difficulté"), "%d%s" % (
                D.difficulty(m),
                "" if m["difficulty"] is None else _(" (forcée)"))),
            (_("Points de vie"), hp),
            (_("Dégâts max/tour"), str(D.max_damage(m))),
            (_("Dégâts moy/tour"), num(D.average_per_turn(m))),
            (_("Vitesse"), "%d (%s)" % (
                m["move"], _("immobile") if not m["move"]
                else _("lent") if m["move"] < 9 else
                _("normal") if m["move"] <= 12 else
                _("rapide") if m["move"] < 18 else _("très rapide"))),
        ]
        st, sa = self.status(m)
        for k, v in lines:
            put(scr, yy, x + 2, k.ljust(16), curses.A_DIM)
            put(scr, yy, x + 18, v, 0, cw - 16)
            yy += 1
        put(scr, yy, x + 2, _("Sources").ljust(16), curses.A_DIM)
        put(scr, yy, x + 18, st, sa, cw - 16)
        yy += 1
        for n, a in enumerate(D.attacks_used(m)):
            avg, msg, _note = D.attack_preview(m, a)
            put(scr, yy, x + 2, _("Attaque %d") % (n + 1), curses.A_DIM)
            put(scr, yy, x + 13, "%5s" % num(avg), 0)
            put(scr, yy, x + 19, msg.replace(D.monnam(m), "…", 1),
                self.colors.fg(curses.COLOR_CYAN), cw - 17)
            yy += 1
        yy += 1
        # vérification
        res = D.validate(m, self.game(), self.others(m))
        if not res:
            put(scr, yy, x + 2, _("✔ aucun problème"),
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

    def fix_after(self, m):
        """Après un changement de classe, « Placer après » ne peut plus
        désigner un monstre de l'ancienne classe."""
        if m["after"] and self.game() and \
                m["after"] not in D.insert_choices(self.game(), m["sym"]):
            m["after"] = ""

    def choices(self, key, m=None):
        if key == "after":
            fr = self.fr_names()
            return [("", _("(fin de la classe)"))] + [
                (n, fr.get(n, ("",))[0])
                for n in D.insert_choices(self.game(), m["sym"])]
        if key == "fr_gender":
            return [("m", _("masculin")), ("f", _("féminin"))]
        if key == "tile_shape":
            return [(c, _("selon la classe") if c == T.SHAPE_AUTO else
                     _("tuile dessinée à la main (t)") if c == T.SHAPE_CUSTOM
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
        elif kind in ("choice", "after"):
            ch = [c for c, _ in self.choices(key, m)]
            i = ch.index(m[key]) if m[key] in ch else 0
            self.checkpoint()
            m[key] = ch[(i + delta) % len(ch)]
            self.fix_after(m)
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
        elif f[0] == "after" and m["after"]:
            self.checkpoint()
            m["after"] = ""

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
                                    _("vide ou inchangé = pluriel calculé "
                                    "(%s)") % auto).strip()
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
            elif kind in ("choice", "after"):
                ch = self.choices(key, m)
                cur = [c for c, _ in ch].index(m[key]) \
                    if m[key] in [c for c, _ in ch] else 0
                shown = [(T.shape_label(c), d) for c, d in ch] \
                    if key == "tile_shape" else ch
                i = self.menu(label, shown, cur, filterable=len(ch) > 8)
                if ch[i][0] != m[key]:
                    self.checkpoint()
                    m[key] = ch[i][0]
                    self.fix_after(m)
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
                    _("vide = calculée automatiquement (%d)") % D.mstrength(m))
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
        k = self.menu(_("Attaque %d : type") % (i + 1), ats, cur)
        at = ats[k][0]
        # les dégâts que le jeu ne gère pas avec ce type sont signalés
        ads = [(n, d if D.attack_allows(at, n) else "✖ " + d +
                _(" (sans effet avec ce type)"))
               for n, _v, d in D.DAMAGE_TYPES]
        names = [n for n, _ in ads]
        cur = names.index(a[1]) if a[1] in D.AD_VALUE and \
            D.attack_allows(at, a[1]) else \
            next(i for i, n in enumerate(names) if D.attack_allows(at, n))
        k = self.menu(_("Attaque %d : dégâts (%s)") % (i + 1, D.AT_DESC[at]),
                      ads, cur)
        ad = ads[k][0]
        dice = "%dd%d" % (a[2] or 1, a[3] or 6)
        while True:
            s = self.input_line(_("Attaque %d : dés") % (i + 1), dice,
                                _("NdM : N dés à M faces (2d6) ; 0d0 pour "
                                "un effet sans dégâts"))
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
                _("La tuile n'apparaît que dans les versions graphiques\n"
                "(Qt, X11), pas dans le terminal. La dessiner quand même ?"),
                _("Tuile")):
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

    def personal_templates(self):
        """Modèles personnels, ou [] (avec un message) si le fichier est
        illisible."""
        try:
            return P.read_templates(P.templates_path())
        except P.ProjectError as e:
            self.msg = str(e)
            return []

    def new_monster(self):
        mine = self.personal_templates()
        items = T.template_list() + [(n, _("(perso) ") + d)
                                     for n, d, _m in mine]
        try:
            i = self.menu(_("Nouveau monstre : modèle"), items)
            nb = len(T.template_list())
            m = T.from_template(i) if i < nb else \
                copy.deepcopy(mine[i - nb][2])
            fr = self.input_line(_("Nom français"), m["fr_name"],
                                 _("nom affiché dans le jeu"))
            en = self.input_line(_("Nom anglais (interne)"), m["name"],
                                 _("en minuscules ; à taper avec ^G en "
                                 "mode wizard"))
        except Cancel:
            return
        m["fr_name"] = fr.strip() or m["fr_name"]
        if en.strip() and en.strip() != m["name"]:
            m["name"] = en.strip()
            m["bn"] = D.derive_bn(m["name"])
        self.add_monster(self.unique_names(m))
        self.msg = _("Monstre créé : %s") % (m["fr_name"] or m["name"])

    def duplicate(self):
        m = self.mon()
        if not m:
            return
        self.add_monster(self.unique_names(copy.deepcopy(m)))
        self.msg = _("Copie créée : %s") % self.mon()["name"]

    def import_game(self):
        game = self.game()
        if not game:
            self.msg = _("Monstres du jeu introuvables dans %s") % self.src
            return
        fr = self.fr_names()
        items = [("%s %s" % (D.CLASS_CHAR.get(g["sym"], "?"),
                             fr.get(g["name"], (g["name"],))[0]),
                  _("%s, niv %d, diff %d") % (g["name"], g["level"],
                                           g["difficulty"]))
                 for g in game]
        try:
            i = self.menu(_("Importer un monstre du jeu (%d)") % len(game),
                          items)
        except Cancel:
            return
        m = self.from_game(game[i])
        self.add_monster(self.unique_names(m))
        self.msg = _("Importé : %s — renommez-le à votre goût") % m["name"]

    def from_game(self, g):
        """Copie d'un monstre du jeu avec son nom français, ses PV de
        golem et sa tuile, comme un monstre du projet."""
        fr = self.fr_names()
        m = D.normalize(copy.deepcopy(g))
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
        return m

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
        if not self.confirm(_("Supprimer « %s » du projet ?\n(il reste dans "
                            "les sources tant que vous n'intégrez pas à "
                            "nouveau)") % (m["fr_name"] or m["name"])):
            return
        self.checkpoint()
        del self.monsters[self.cur]
        self.cur = max(0, min(self.cur, len(self.monsters) - 1))
        self.msg = _("Supprimé")

    def goto_monster(self):
        """/ : aller à un monstre ; les lettres tapées filtrent la liste
        (nom français, nom anglais, identifiant)."""
        if not self.monsters:
            self.msg = _("Aucun monstre dans le projet")
            return
        items = [("%s %s" % (D.CLASS_CHAR.get(m["sym"], "?"),
                             m["fr_name"] or m["name"]),
                  "%s, PM_%s" % (m["name"], m["bn"]))
                 for m in self.monsters]
        try:
            self.cur = self.menu(_("Aller au monstre (%d) — tapez son nom") %
                                 len(items), items, self.cur)
        except Cancel:
            return
        self.focus = "list"

    def move_monster(self, delta):
        j = self.cur + delta
        if not self.monsters or not 0 <= j < len(self.monsters):
            return
        self.checkpoint()
        ms = self.monsters
        ms[self.cur], ms[j] = ms[j], ms[self.cur]
        self.cur = j

    # --- sauvegarde de secours -------------------------------------------

    def autosave(self, force=False):
        """Écrit projet.json.nhmonedit-autosave si le projet est modifié
        et que la dernière sauvegarde de secours date de plus de
        autosave_delay secondes."""
        now = time.time()
        if not self.modified or self.autosave_delay <= 0:
            return
        if not force and now - self.autosave_time < self.autosave_delay:
            return
        self.autosave_time = now
        try:
            P.write_project(P.autosave_path(self.project), self.monsters)
        except OSError:
            pass        # une sauvegarde de secours ratée ne doit pas
            #             gêner l'édition

    def offer_autosave(self):
        """Au lancement : propose de récupérer une sauvegarde de secours
        plus récente que le projet."""
        auto = P.pending_autosave(self.project)
        if not auto:
            return
        when = time.strftime("%d/%m/%Y %H:%M",
                             time.localtime(os.path.getmtime(auto)))
        if not self.confirm(_("Sauvegarde de secours du %s trouvée\n"
                              "(session interrompue). La récupérer ?") % when,
                            _("Sauvegarde de secours")):
            P.drop_autosave(self.project)
            return
        try:
            monsters = P.read_monsters(auto)
        except P.ProjectError as e:
            self.msg = _("Sauvegarde de secours illisible : %s") % e
            return
        self.checkpoint()
        self.monsters, self.cur = monsters, 0
        self.msg = _("Sauvegarde de secours récupérée (%d monstres) — s pour "
                     "enregistrer") % len(monsters)

    # --- projet -----------------------------------------------------------

    def project_menu(self):
        """p : actions sur les fichiers du projet."""
        actions = [
            (_("Fusionner un autre projet…"),
             _("ajoute ses monstres à la fin de la liste"), self.merge),
            (_("Exporter le monstre…"),
             _("un fichier .nhmon.json à échanger"), self.export_monster),
            (_("Importer un monstre exporté…"),
             _("fichier .nhmon.json"), self.import_monster),
            (_("Enregistrer le monstre comme modèle…"),
             _("proposé ensuite par n"), self.save_template),
            (_("Supprimer un modèle personnel…"),
             P.templates_path().replace(os.path.expanduser("~"), "~", 1),
             self.delete_template),
        ]
        try:
            i = self.menu(_("Projet : %s") % os.path.basename(self.project),
                          [(a, b) for a, b, _f in actions], filterable=False)
        except Cancel:
            return
        actions[i][2]()

    def choose_file(self, title, suffix):
        """Choix d'un fichier *suffix (dossier du projet, de l'éditeur,
        dossier courant) ou d'un chemin saisi. Lève Cancel."""
        dirs = [os.path.dirname(self.project), HERE, os.getcwd()]
        files = [(n, d) for n, d in P.json_files(dirs, suffix)
                 if os.path.join(d, n) != self.project]
        home = os.path.expanduser("~")
        items = [(n, d.replace(home, "~", 1)) for n, d in files] + \
            [(_("Autre fichier…"), "")]
        i = self.menu(title, items)
        if i < len(files):
            return os.path.join(files[i][1], files[i][0])
        path = self.input_line(title, os.path.dirname(self.project) + "/",
                               _("chemin du fichier"))
        return os.path.abspath(os.path.expanduser(path.strip()))

    def merge(self):
        """Ajoute les monstres d'un autre projet ; ceux qui existent déjà
        à l'identique sont ignorés, les noms déjà pris sont renommés."""
        try:
            path = self.choose_file(_("Fusionner un projet"), ".json")
            new = P.read_monsters(path)
        except Cancel:
            return
        except P.ProjectError as e:
            self.message_box(_("Fusion impossible"), [str(e)])
            return
        added, same = self.add_monsters(new)
        self.msg = _("Fusion : %d monstre(s) ajouté(s), %d déjà "
                     "présent(s)") % (added, same)

    def export_monster(self):
        m = self.mon()
        if not m:
            self.msg = _("Aucun monstre dans le projet")
            return
        try:
            path = self.input_line(
                _("Exporter « %s »") % (m["fr_name"] or m["name"]),
                P.export_path(os.path.dirname(self.project), m),
                _("fichier à créer (se relit avec « Importer un monstre "
                  "exporté »)")).strip()
        except Cancel:
            return
        path = os.path.abspath(os.path.expanduser(path))
        if os.path.exists(path) and not self.confirm(
                _("%s existe déjà. Le remplacer ?") % path):
            return
        try:
            P.write_monster(path, m)
        except OSError as e:
            self.message_box(_("Export impossible"), [str(e)])
            return
        self.msg = _("Exporté : %s") % path

    def import_monster(self):
        try:
            path = self.choose_file(_("Importer un monstre exporté"),
                                    P.MONSTER_SUFFIX)
            new = P.read_monsters(path)
        except Cancel:
            return
        except P.ProjectError as e:
            self.message_box(_("Import impossible"), [str(e)])
            return
        added, _same = self.add_monsters(new)
        self.msg = _("Importé : %s") % (self.mon()["name"] if added else
                                        _("déjà dans le projet"))

    def save_template(self):
        m = self.mon()
        if not m:
            self.msg = _("Aucun monstre dans le projet")
            return
        mine = self.personal_templates()
        name = m["fr_name"] or m["name"]
        try:
            name = self.input_line(_("Nom du modèle"),
                                   name[:1].upper() + name[1:],
                                   _("affiché dans le menu de n")).strip()
            desc = self.input_line(_("Description du modèle"), "",
                                   _("facultative : ce qui le distingue"))
        except Cancel:
            return
        if not name:
            return
        old = [i for i, (n, _d, _m) in enumerate(mine) if n == name]
        if old and not self.confirm(_("Le modèle « %s » existe déjà. Le "
                                      "remplacer ?") % name):
            return
        tpl = (name, desc.strip(), copy.deepcopy(m))
        if old:
            mine[old[0]] = tpl
        else:
            mine.append(tpl)
        try:
            P.write_templates(P.templates_path(), mine)
        except OSError as e:
            self.message_box(_("Enregistrement impossible"), [str(e)])
            return
        self.msg = _("Modèle enregistré : %s — proposé par n") % name

    def delete_template(self):
        mine = self.personal_templates()
        if not mine:
            self.msg = _("Aucun modèle personnel")
            return
        try:
            i = self.menu(_("Supprimer un modèle personnel"),
                          [(n, d) for n, d, _m in mine])
        except Cancel:
            return
        if not self.confirm(_("Supprimer le modèle « %s » ?") % mine[i][0]):
            return
        name = mine.pop(i)[0]
        try:
            P.write_templates(P.templates_path(), mine)
        except OSError as e:
            self.message_box(_("Enregistrement impossible"), [str(e)])
            return
        self.msg = _("Modèle supprimé : %s") % name

    def add_monsters(self, new):
        """Ajoute des monstres à la fin du projet. Renvoie (ajoutés,
        identiques ignorés)."""
        fresh = [m for m in new
                 if not any(P.same_monster(m, o) for o in self.monsters)]
        if fresh:
            self.checkpoint()
            for m in fresh:
                self.monsters.append(self.unique_names(m))
            self.cur = len(self.monsters) - 1
        return len(fresh), len(new) - len(fresh)

    # --- vues -------------------------------------------------------------

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
        self.viewer(_("Code de %s") % m["name"], lines)

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
                lines.append((_("   ✔ aucun problème"),
                              self.colors.fg(curses.COLOR_GREEN, True)))
            for g, msg in res:
                lines.append(("   %s %s" % ("✖" if g == "erreur" else "⚠",
                                            msg),
                              self.colors.fg(curses.COLOR_RED, True)
                              if g == "erreur" else
                              self.colors.fg(curses.COLOR_YELLOW, True)))
            lines.append("")
        if not self.monsters:
            lines = [_("Aucun monstre dans le projet.")]
        self.viewer(_("Vérification : %d erreur(s)") % nerr, lines)
        return nerr

    def show_compare(self):
        m = self.mon()
        if not m:
            return
        d = D.difficulty(m)
        fr = self.fr_names()
        near = sorted(self.game(), key=lambda g: (abs(g["difficulty"] - d),
                                                  g["level"]))[:30]
        lines = [(_("Monstres du jeu de difficulté proche de %d :") % d,
                  curses.A_BOLD), "",
                 _("    nom                         niv  vit  CA  diff  "
                 "dégâts max"), ""]
        for g in sorted(near, key=lambda g: g["difficulty"]):
            name = fr.get(g["name"], (g["name"],))[0]
            lines.append((" %s  %-27s %3d  %3d %3d  %4d  %5d" % (
                D.CLASS_CHAR.get(g["sym"], "?"), name[:27], g["level"],
                g["move"], g["ac"], g["difficulty"], D.max_damage(g)),
                self.colors.mon(g["color"])))
        lines += ["", (" ▶ %-28s %3d  %3d %3d  %4d  %5d" % (
            (m["fr_name"] or m["name"])[:28], m["level"], m["move"],
            m["ac"], d, D.max_damage(m)), curses.A_BOLD)]
        self.viewer(_("Comparaison"), lines)

    def show_side_by_side(self):
        """B : fiche comparée avec un autre monstre du projet ou du jeu."""
        m = self.mon()
        if not m:
            return
        fr = self.fr_names()
        others = [(o, "projet") for o in self.others(m)] + \
            [(g, "jeu") for g in self.game()]
        items = [("%s %s" % (D.CLASS_CHAR.get(o["sym"], "?"),
                             (o.get("fr_name") or
                              fr.get(o["name"], (o["name"],))[0])),
                  _("%s, %s, niv %d") % ({"projet": _("projet"),
                                          "jeu": _("jeu")}[where],
                                         o["name"], o["level"]))
                 for o, where in others]
        # monstre d'origine d'un import (« soldier ant mk II »)
        base = re.sub(r" mk [IVX\d]+$", "", m["name"])
        cur = next((i for i, (o, w) in enumerate(others)
                    if w == "jeu" and o["name"] == base), 0)
        try:
            i = self.menu(_("Comparer « %s » à…") % (m["fr_name"] or
                                                     m["name"]),
                          items, cur)
        except Cancel:
            return
        o, where = others[i]
        if where == "jeu":
            o = self.from_game(o)
        W = self.stdscr.getmaxyx()[1]
        lines, ndiff = self.compare_lines(m, o, min(W - 2, 110) - 4)
        self.viewer(_("Fiche comparée : %d différence(s)") % ndiff, lines)

    def compare_lines(self, a, b, width):
        """Lignes de la fiche comparée (valeurs différentes en jaune) et
        nombre de différences."""
        cw = (width - 26) // 2
        diff_attr = self.colors.fg(curses.COLOR_YELLOW, True)

        def row(label, va, vb, differ):
            return ("%s %-20s %s │ %s" % ("≠" if differ else " ", label[:20],
                                          clip(va, cw).ljust(cw),
                                          clip(vb, cw)),
                    diff_attr if differ else 0)
        lines = [("  %-20s %s │ %s" % ("", clip(a["fr_name"] or a["name"],
                                                  cw).ljust(cw),
                                        clip(b["fr_name"] or b["name"], cw)),
                  curses.A_BOLD)]
        ndiff = 0
        for f in FIELDS:
            if f[0] == "section":
                lines += ["", ("▸ " + f[2], self.accent())]
                continue
            key = f[1]
            if f[0] == "attack":
                differ = a["attacks"][key] != b["attacks"][key]
            elif f[0] == "difficulty":
                differ = D.difficulty(a) != D.difficulty(b)
            elif f[0] == "plural":
                differ = self.field_value(a, f)[0] != \
                    self.field_value(b, f)[0]
            else:
                differ = a[key] != b[key]
            ndiff += differ
            lines.append(row(f[2].strip(), self.field_value(a, f)[0],
                             self.field_value(b, f)[0], differ))
        lines += ["", (_("▸ Calculs"), self.accent())]
        for label, fn in ((_("Points de vie"), hp_text),
                          (_("Dégâts max/tour"),
                           lambda m: str(D.max_damage(m)))):
            va, vb = fn(a), fn(b)
            lines.append(row(label, va, vb, va != vb))
        return lines, ndiff

    def help(self):
        self.viewer(_("Aide"), HELP)

    # --- sources -------------------------------------------------------------

    def check_src(self):
        err = I.check_tree(self.src)
        if err:
            self.message_box(_("Sources introuvables"), [
                err, "", _("Indiquez le dossier des sources avec --src ou "
                "la variable NHMONEDIT_SRC.")])
            return False
        return True

    def integrate(self):
        if not self.check_src():
            return
        if not self.monsters:
            self.msg = _("Aucun monstre à intégrer (R pour retirer)")
            return
        errs = []
        for m in self.monsters:
            for g, msg in D.validate(m, self.game(), self.others(m)):
                if g == "erreur":
                    errs.append("%s : %s" % (m["name"], msg))
        if errs:
            self.viewer(_("Intégration impossible : corrigez d'abord"),
                        errs)
            return
        fixes = ""
        if os.path.isfile(os.path.join(self.src, I.FIXES)):
            old = I.fixes_entry(I._read(self.src, I.FIXES))
            try:
                fixes = self.input_line(
                    _("Entrée de %s") % I.FIXES,
                    old or I.default_fixes(self.monsters),
                    _("« %s… » ; vide : pas d'entrée") % I.FIXES_PREFIX)
            except Cancel:
                return
        try:
            files = I.plan(self.src, self.monsters, fixes)
        except I.InstallError as e:
            self.message_box(_("Intégration impossible"), [str(e)])
            return
        diff = I.diff(self.src, files)
        if not diff:
            self.msg = _("Les sources sont déjà à jour")
            return
        lines = []
        for l in diff.split("\n"):
            a = self.colors.fg(curses.COLOR_GREEN) if l.startswith("+") \
                else self.colors.fg(curses.COLOR_RED) if l.startswith("-") \
                else self.cyan() if l.startswith("@@") else 0
            lines.append((l, a))
        self.viewer(_("Aperçu des changements (q pour continuer)"), lines)
        changed = [r for r, t in files.items()
                   if open(os.path.join(self.src, r),
                           encoding="utf-8").read() != t]
        if not self.confirm(_("Écrire dans les sources (%s) ?\n\n%s\n\n"
                            "Une copie des fichiers va dans sauvegardes/."
                            "\nSi la liste des monstres change, EDITLEVEL "
                            "augmente :\nles anciennes sauvegardes ne se "
                            "chargeront plus.") % (
                                self.src, "\n".join("  " + c
                                                    for c in changed))):
            return
        ch, lvl, bk = I.apply(self.src, files, True, BACKUP_DIR)
        self._game = None
        self._inst = (None, {})
        if self.modified:
            self.save()
        self.msg = _("Intégré : %d fichier(s)%s — m pour compiler") % (
            len(ch), _(", EDITLEVEL %d") % lvl if lvl is not None else "")
        self.offer_commit(ch, I.commit_message(self.monsters))

    def offer_commit(self, changed, message):
        """Après une intégration ou un retrait : commit git des fichiers
        touchés, si les sources sont un dépôt git."""
        if not changed or not I.is_git_repo(self.src):
            return
        try:
            message = self.input_line(
                _("Commit dans les sources ? (Échap : non)"), message,
                _("message du commit des %d fichier(s) modifié(s)")
                % len(changed)).strip()
        except Cancel:
            return
        if not message:
            return
        ok, out = I.git_commit(self.src, changed, message)
        if ok:
            self.msg = _("Commit créé dans les sources : %s") % \
                out.split("\n")[0]
        else:
            self.message_box(_("Commit impossible"), out.split("\n")[-12:])

    def sources_menu(self):
        """R : retirer les monstres, ou rétablir une sauvegarde."""
        try:
            i = self.menu(_("Retirer des sources"), [
                (_("Retirer les monstres de l'éditeur"),
                 _("rend les fichiers d'origine (EDITLEVEL + 1)")),
                (_("Rétablir une sauvegarde…"),
                 _("annule une intégration : fichiers de sauvegardes/"))],
                filterable=False)
        except Cancel:
            return
        if i == 0:
            self.remove()
        else:
            self.restore_backup()

    def restore_backup(self):
        """Remet dans les sources les fichiers d'un dossier de
        sauvegardes/ (l'état d'avant une intégration ou un retrait)."""
        if not self.check_src():
            return
        backups = I.list_backups(BACKUP_DIR)
        if not backups:
            self.msg = _("Aucune sauvegarde dans %s") % BACKUP_DIR
            return
        items = []
        for d, files in backups:
            n = os.path.basename(d)
            when = "%s/%s/%s %s:%s:%s" % (n[6:8], n[4:6], n[:4], n[9:11],
                                          n[11:13], n[13:15]) \
                if re.match(r"\d{8}-\d{6}$", n) else n
            items.append((when, _("%d fichier(s), d'avant l'écriture de "
                                  "ce moment-là") % len(files)))
        try:
            i = self.menu(_("Rétablir une sauvegarde"), items,
                          filterable=False)
        except Cancel:
            return
        files = I.restore_plan(self.src, backups[i][0])
        if not files:
            self.msg = _("Les sources sont déjà dans cet état")
            return
        lines = []
        for l in I.diff(self.src, files).split("\n"):
            a = self.colors.fg(curses.COLOR_GREEN) if l.startswith("+") \
                else self.colors.fg(curses.COLOR_RED) if l.startswith("-") \
                else self.cyan() if l.startswith("@@") else 0
            lines.append((l, a))
        self.viewer(_("Changements du rétablissement (q pour continuer)"),
                    lines)
        if not self.confirm(_("Rétablir dans les sources (%s) ?\n\n%s\n\n"
                              "L'état actuel est d'abord copié dans "
                              "sauvegardes/.") % (
                                  self.src, "\n".join("  " + r
                                                      for r in files))):
            return
        ch, _lvl, _bk = I.apply(self.src, files, False, BACKUP_DIR)
        self._game = None
        self._inst = (None, {})
        self.msg = _("Sauvegarde du %s rétablie : %d fichier(s)") % (
            items[i][0], len(ch))
        self.offer_commit(ch, "Restore the sources from the nhmonedit "
                          "backup of %s" % items[i][0])

    def remove(self):
        if not self.check_src():
            return
        ids = I.installed_ids(self.src)
        if not ids:
            self.msg = _("Aucun monstre de l'éditeur dans les sources")
            return
        if not self.confirm(_("Retirer des sources les %d monstres ajoutés "
                            "par l'éditeur ?\n%s") % (len(ids), ", ".join(
                                ids))):
            return
        ch, lvl, bk = I.uninstall(self.src, True, BACKUP_DIR)
        self._game = None
        self._inst = (None, {})
        self.msg = _("Retiré de %d fichier(s)") % len(ch)
        self.offer_commit(ch, I.commit_message([]))

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
        print(_("\n\033[1;%sm== terminé (code %d, %.0f s) ==\033[0m")
              % (color, rc, time.time() - t))
        try:
            input(_("Entrée pour revenir à l'éditeur… "))
        except (EOFError, KeyboardInterrupt):
            pass
        curses.reset_prog_mode()
        self.stdscr.clear()
        curses.curs_set(0)
        enable_mouse()
        return rc

    def make(self):
        if not self.check_src():
            return
        if not os.path.isfile(os.path.join(self.src, "Makefile")):
            self.message_box(_("Sources non configurées"), [
                _("Pas de Makefile : configurez d'abord les sources :"),
                "  cd sys/unix && sh setup.sh hints/linux.500"])
            return
        opts = self.config.get("make") or "-j%d" % (os.cpu_count() or 2)
        rc = self.run_external(_("compilation"), "make " + opts, self.src)
        self.msg = _("Compilation réussie — U pour mettre à jour le jeu") \
            if rc == 0 else _("La compilation a échoué (code %d)") % rc

    def make_update(self):
        if not self.check_src():
            return
        if not self.confirm(
                _("Mettre à jour le jeu installé (make update) ?\n\n"
                "sysconf, scores et dossier save sont conservés ;\n"
                "le jeu précédent est gardé en nethack.old.")):
            return
        rc = self.run_external(_("mise à jour du jeu"), "make update",
                               self.src)
        self.msg = _("Jeu mis à jour — j pour l'essayer") if rc == 0 \
            else _("make update a échoué (code %d)") % rc

    # --- souris -------------------------------------------------------------

    def mouse(self, ev):
        """Clic : choisir un monstre ou un champ ; double clic : ouvrir
        la fiche ou modifier le champ ; molette : faire défiler."""
        for zone, (y, x, h, w) in self.areas.items():
            if y < ev.y < y + h - 1 and x < ev.x < x + w - 1:
                break
        else:
            return
        if not self.monsters:
            return
        row = ev.y - y - 1
        if zone == "list":
            self.focus = "list"
            if wheel(ev):
                self.cur = max(0, min(len(self.monsters) - 1,
                                      self.cur + 3 * wheel(ev)))
            elif ev.kind in ("click", "double") and \
                    self.list_top + row < len(self.monsters):
                self.cur = self.list_top + row
                if ev.kind == "double":
                    self.focus = "form"
        else:
            self.focus = "form"
            if wheel(ev):
                for _i in range(3):
                    self.move_field(wheel(ev))
            elif ev.kind in ("click", "double"):
                i = self.form_top + row
                if i < len(FIELDS) and FIELDS[i][0] != "section":
                    self.field = i
                    if ev.kind == "double":
                        self.edit_field()

    # --- boucle -------------------------------------------------------------

    def quit(self):
        if not self.modified:
            return True
        try:
            i = self.menu(_("Projet modifié"), [
                (_("Enregistrer et quitter"), ""),
                (_("Quitter sans enregistrer"), ""),
                (_("Annuler"), "")], filterable=False)
        except Cancel:
            return False
        if i == 0:
            self.save()
            return True
        return i == 1

    def run(self):
        curses.curs_set(0)
        self.stdscr.keypad(True)
        self.stdscr.timeout(5000)   # réveil pour la sauvegarde de secours
        enable_mouse()
        self.draw()
        self.offer_autosave()
        while True:
            self.autosave()
            self.draw()
            k = get_key(self.stdscr, idle=True)
            if k is None:
                continue
            if k != curses.KEY_RESIZE:
                self.msg = ""
            if k == curses.KEY_RESIZE:
                continue
            if isinstance(k, Mouse):
                self.mouse(k)
            elif k == "q":
                if self.quit():
                    P.drop_autosave(self.project)
                    return
            elif k == "?":
                self.help()
            elif k == "s":
                self.save()
            elif k == "u":
                self.undo()
            elif k in ("\x12", "\x19"):
                self.undo(redo=True)
            elif k == "n":
                self.new_monster()
            elif k == "d":
                self.duplicate()
            elif k == "i":
                self.import_game()
            elif k == "t":
                self.edit_tile()
            elif k == "/":
                self.goto_monster()
            elif k == "p":
                self.project_menu()
            elif k == "v":
                self.show_validation()
            elif k == "c":
                self.show_code()
            elif k == "b":
                self.show_compare()
            elif k == "B":
                self.show_side_by_side()
            elif k == "I":
                self.integrate()
            elif k == "R":
                self.sources_menu()
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
            for _i in range(10):
                self.move_field(-1)
        elif k == curses.KEY_NPAGE:
            for _i in range(10):
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


def parse_args(argv, config=None):
    """(projet, sources) : ligne de commande, puis NHMONEDIT_SRC, puis
    la configuration, puis les valeurs par défaut."""
    config = config or {}
    project = config.get("project", DEFAULT_PROJECT)
    src = os.environ.get("NHMONEDIT_SRC") or config.get("src", DEFAULT_SRC)
    args = list(argv)
    while args:
        a = args.pop(0)
        if a in ("-h", "--help"):
            print(_(__doc__.strip()))
            sys.exit(0)
        elif a == "--src" and args:
            src = args.pop(0)
        elif a.startswith("--src="):
            src = a.split("=", 1)[1]
        elif a.startswith("-"):
            sys.exit(_("Option inconnue : %s (voir --help)") % a)
        else:
            project = a
    return os.path.abspath(project), os.path.abspath(src)


def main(argv=None):
    config, errs = C.load(C.default_path())
    project, src = parse_args(sys.argv[1:] if argv is None else argv,
                              config)
    os.environ.setdefault("ESCDELAY", "25")
    if "mouse" in config:
        os.environ.setdefault("NHMONEDIT_MOUSE", "1" if config["mouse"]
                              else "0")
    import locale
    locale.setlocale(locale.LC_ALL, "")
    curses.wrapper(lambda scr: Editor(scr, project, src, config,
                                      errs).run())


if __name__ == "__main__":
    main()
