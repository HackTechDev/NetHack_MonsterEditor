"""Tests de nhmonedit : lecture de monsters.h, difficulté, code C et
intégration dans une copie des sources.

python3 -m unittest discover -s tests   (depuis le dossier de l'éditeur)
Les sources sont cherchées dans ../NetHack-5.0.0 ou $NHMONEDIT_SRC.
"""

import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
os.environ["NHMONEDIT_LANG"] = "fr"     # messages vérifiés en français

import nhmon_config as C  # noqa: E402
import nhmon_data as D  # noqa: E402
import nhmon_install as I  # noqa: E402
import nhmon_project as P  # noqa: E402
import nhmon_templates as T  # noqa: E402
import nhmonedit as E  # noqa: E402
import nhmon_ui as U  # noqa: E402

SRC = os.environ.get("NHMONEDIT_SRC") or os.path.normpath(
    os.path.join(HERE, "..", "..", "NetHack-5.0.0"))
HAVE_SRC = os.path.isfile(os.path.join(SRC, I.MONSTERS_H))


@unittest.skipUnless(HAVE_SRC, "sources de NetHack absentes")
class TestGameData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.game = I.game_monsters(SRC)

    def test_count(self):
        self.assertGreater(len(self.game), 350)

    def test_known_constants(self):
        for m in self.game:
            for f in ("mr1", "mr2", "geno", "flags1", "flags2", "flags3"):
                for n in m[f]:
                    self.assertIn(n, D.FLAG_VALUE, m["name"])
            for at, ad, _n, _d in m["attacks"]:
                self.assertIn(at, D.AT_VALUE)
                self.assertIn(ad, D.AD_VALUE)
            self.assertIn(m["color"], D.COLOR_VALUE)

    def test_difficulty_matches_game(self):
        """mstrength() calcule la difficulté codée dans le jeu (sauf les
        quelques valeurs ajustées à la main)."""
        bad = [m["name"] for m in self.game
               if D.mstrength(m) != m["difficulty"]]
        self.assertLessEqual(len(bad), 3, bad)

    def test_c_entry_roundtrip(self):
        keys = ("name", "name_m", "name_f", "sym", "level", "move", "ac",
                "mr", "align", "freq", "geno", "attacks", "weight",
                "nutrition", "sound", "mr1", "mr2", "flags1", "flags2",
                "flags3", "difficulty", "color", "bn")
        for m in self.game:
            code = D.c_entry(m, marker=False)
            for line in code.split("\n"):
                self.assertLessEqual(len(line), 78, line)
            _s, _e, args = next(D.iter_mon_calls(code))
            p = D.parse_mon(args)
            for k in keys:
                self.assertEqual(p[k], m[k], (m["name"], k))

    def test_game_attacks_accepted(self):
        """Aucune combinaison d'attaque du jeu n'est signalée."""
        for m in self.game:
            self.assertEqual(D.check_attacks(m), [], m["name"])

    def test_french_names(self):
        fr = D.french_names(SRC)
        self.assertIn("iron golem", fr)


class TestTemplates(unittest.TestCase):
    def test_tiles(self):
        for name, shape in T.SHAPES.items():
            self.assertEqual(len(shape), D.TILE_SIZE, name)
            for row in shape:
                self.assertEqual(len(row), D.TILE_SIZE, name)

    def test_templates_valid(self):
        ms = [T.from_template(i) for i in range(len(T.TEMPLATES))]
        for m in ms:
            errs = [x for g, x in D.validate(m, [], []) if g == "erreur"]
            self.assertEqual(errs, [], m["name"])

    def test_tile_for(self):
        for i in range(len(T.TEMPLATES)):
            m = T.from_template(i)
            tile = T.tile_for(m)
            self.assertEqual(len(tile), D.TILE_SIZE)
            self.assertTrue(any(c != "." for r in tile for c in r))
            self.assertTrue(all(c in dict(D.TILE_PALETTE)
                                for r in tile for c in r))
        m = D.new_monster()
        m["sym"] = "S_GIANT"
        self.assertEqual(T.shape_of(m), "mecha")
        m["tile_shape"] = T.SHAPE_CUSTOM
        m["tile"][0] = "A" * D.TILE_SIZE
        self.assertEqual(T.tile_for(m)[0], "A" * D.TILE_SIZE)

    def test_old_project_keeps_drawn_tile(self):
        m = D.new_monster()
        del m["tile_shape"]
        m["tile"][3] = "B" * D.TILE_SIZE
        self.assertEqual(D.normalize(m)["tile_shape"], T.SHAPE_CUSTOM)

    def test_attack_combinations(self):
        def grav(*attacks):
            m = D.new_monster()
            m["attacks"] = [list(a) for a in attacks] + [
                list(D.NO_ATTK) for _ in range(D.NATTK - len(attacks))]
            return [g for g, _ in D.check_attacks(m)]
        self.assertEqual(grav(("AT_BREA", "AD_PLYS", 2, 6)), ["erreur"])
        self.assertEqual(grav(("AT_BREA", "AD_FIRE", 2, 6)), [])
        self.assertEqual(grav(("AT_SPIT", "AD_FIRE", 1, 6)), ["erreur"])
        self.assertEqual(grav(("AT_GAZE", "AD_SLEE", 1, 6)), ["erreur"])
        self.assertEqual(grav(("AT_EXPL", "AD_ACID", 4, 6)), ["erreur"])
        self.assertEqual(grav(("AT_MAGC", "AD_ELEC", 0, 0)), ["erreur"])
        self.assertEqual(grav(("AT_ENGL", "AD_PLYS", 1, 4)), ["attention"])
        self.assertEqual(grav(("AT_NONE", "AD_SLEE", 1, 4)), ["attention"])
        self.assertEqual(grav(("AT_CLAW", "AD_SPEL", 1, 4)), ["attention"])
        self.assertEqual(grav(("AT_HUGS", "AD_PHYS", 2, 6)), ["attention"])
        self.assertEqual(grav(("AT_CLAW", "AD_PHYS", 1, 4),
                              ("AT_CLAW", "AD_PHYS", 1, 4),
                              ("AT_HUGS", "AD_PHYS", 2, 6)), [])
        self.assertTrue(D.attack_allows("AT_CLAW", "AD_ELEC"))
        self.assertFalse(D.attack_allows("AT_BREA", "AD_PLYS"))

    def test_french_plural(self):
        P = D.french_plural
        self.assertEqual(P("mecha de combat"), "mechas de combat")
        self.assertEqual(P("drone d'assaut"), "drones d'assaut")
        self.assertEqual(P("araignée-robot"), "araignées-robots")
        self.assertEqual(P("loup-garou"), "loups-garous")
        self.assertEqual(P("nymphe des eaux"), "nymphes des eaux")
        self.assertEqual(P("jeu"), "jeux")
        self.assertEqual(P("robot à vapeur"), "robots à vapeur")
        # comme le jeu : la règle se trompe, le contrôle le signale
        self.assertEqual(P("sentinelle Arasaka"), "sentinelles Arasakas")
        self.assertTrue(D.plural_doubts("sentinelle Arasaka"))
        self.assertTrue(D.plural_doubts("cheval mécanique"))
        self.assertTrue(D.plural_doubts("IA corrompue"))
        self.assertFalse(D.plural_doubts("mecha de combat"))

    def test_plural_po_entry(self):
        m = T.from_template(0)
        self.assertNotIn("monster-plural",
                         "".join(I.po_entries(m, "cyber")))
        m["fr_plural"] = "robots de sécurité"
        cyber = "".join(I.po_entries(m, "cyber"))
        self.assertIn('msgctxt "monster-plural"\nmsgid "security bot"\n'
                      'msgstr "robots de sécurité"', cyber)
        self.assertNotIn("monster-plural", "".join(I.po_entries(m, "fr")))

    def test_attack_preview(self):
        m = T.from_template(0)
        m["fr_name"], m["fr_gender"] = "sentinelle Arasaka", "f"
        avg, msg, _n = D.attack_preview(m, ["AT_WEAP", "AD_PHYS", 2, 6])
        self.assertEqual(avg, 7.0)
        self.assertEqual(msg, "La sentinelle Arasaka frappe !")
        m["fr_name"] = "androïde"
        _a, msg, _n = D.attack_preview(m, ["AT_BREA", "AD_FIRE", 4, 6])
        self.assertEqual(msg, "L'androïde crache du feu !")
        self.assertEqual(D.average_per_turn(
            dict(m, attacks=[["AT_CLAW", "AD_PHYS", 1, 4],
                             ["AT_BOOM", "AD_FIRE", 4, 6]])), 2.5)

    def test_derive_bn(self):
        self.assertEqual(D.derive_bn("araignée-robot"), "ARAIGNEE_ROBOT")
        self.assertEqual(D.derive_bn("2 bots"), "M_2_BOTS")


@unittest.skipUnless(HAVE_SRC, "sources de NetHack absentes")
class TestInstall(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="nhmonedit-")
        for rel in I.ALL_FILES:
            p = os.path.join(SRC, rel)
            if os.path.isfile(p):
                q = os.path.join(self.tmp, rel)
                os.makedirs(os.path.dirname(q), exist_ok=True)
                shutil.copy(p, q)
        # le dossier de test part de sources sans monstres de l'éditeur
        I.uninstall(self.tmp, bump=False)
        self.orig = {rel: open(os.path.join(self.tmp, rel),
                               encoding="utf-8").read()
                     for rel in I.ALL_FILES
                     if os.path.isfile(os.path.join(self.tmp, rel))}

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_install_and_remove(self):
        ms = [T.from_template(i) for i in range(len(T.TEMPLATES) - 1)]
        changed, level, _bk = I.install(self.tmp, ms)
        self.assertIn(I.MONSTERS_H, changed)
        self.assertIsNotNone(level)
        self.assertEqual(sorted(I.installed_ids(self.tmp)),
                         sorted(m["bn"] for m in ms))
        # les classes restent contiguës : autant de blocs par classe
        # qu'avant (les némésis de fin de liste forment des blocs à part)
        def blocks(text):
            syms = []
            for _s, _e, a in D.iter_mon_calls(text):
                if len(a) == 14 and (not syms or syms[-1] != a[1]):
                    syms.append(a[1])
            return sorted(syms)
        self.assertEqual(blocks(open(os.path.join(
            self.tmp, I.MONSTERS_H), encoding="utf-8").read()),
            blocks(self.orig[I.MONSTERS_H]))
        # deux monstres de même classe : blocs non imbriqués
        text = open(os.path.join(self.tmp, I.MONSTERS_H),
                    encoding="utf-8").read()
        self.assertNotRegex(text, r"begin SECURITY_BOT \*/\n(?:(?!end "
                            r"SECURITY_BOT).)*begin SECURITY_TURRET")
        # une deuxième intégration identique ne change rien
        self.assertEqual(I.install(self.tmp, ms)[0], [])
        # retrait : fichiers d'origine (sauf EDITLEVEL)
        I.uninstall(self.tmp)
        for rel, t in self.orig.items():
            if rel != I.PATCHLEVEL:
                self.assertEqual(open(os.path.join(self.tmp, rel),
                                      encoding="utf-8").read(), t, rel)

    def test_tiles_follow_mons_order(self):
        ms = [T.from_template(i) for i in range(len(T.TEMPLATES) - 1)]
        I.install(self.tmp, ms)
        h = open(os.path.join(self.tmp, I.MONSTERS_H),
                 encoding="utf-8").read()
        names = [D.parse_mon(a)["name"] for _s, _e, a in
                 D.iter_mon_calls(h) if len(a) == 14]
        tiles = open(os.path.join(self.tmp, I.TILES),
                     encoding="utf-8").read()
        tnames = [mo.group(3).rsplit(",", 1)[0]
                  for mo in I.TILE_HDR.finditer(tiles)
                  if mo.group(3).endswith(",male")]
        # les tuiles des monstres du jeu suivent mons[] (en sautant les
        # tuiles de monstres désactivés)
        it = iter(tnames)
        for n in names:
            if n == "long worm tail":
                break
            for t in it:
                if t == n:
                    break
            else:
                self.fail("tuile de %s absente ou mal placée" % n)

    def test_insert_after(self):
        game = I.game_monsters(SRC)
        golems = D.insert_choices(game, "S_GOLEM")
        self.assertIn("iron golem", golems)
        dragons = D.insert_choices(game, "S_DRAGON")
        self.assertNotIn("gray dragon", dragons)
        self.assertIn("yellow dragon", dragons)
        self.assertNotIn("archeologist", D.insert_choices(game, "S_HUMAN"))
        a, b = T.from_template(0), T.from_template(10)
        a["after"] = b["after"] = "iron golem"
        b["name"], b["bn"] = "blank bot", "BLANK_BOT"
        files = I.plan(self.tmp, [a, b])
        order = [g["name"] for g in I.game_monsters(self.tmp)]
        text = files[I.MONSTERS_H]
        names = [D.parse_mon(args)["name"] for _s, _e, args in
                 D.iter_mon_calls(text) if len(args) == 14]
        i = names.index("iron golem")
        self.assertEqual(names[i:i + 4], ["iron golem", "security bot",
                                          "blank bot",
                                          order[order.index("iron golem")
                                                + 1]])
        tiles = files[I.TILES]
        self.assertLess(tiles.index("(iron golem,female)"),
                        tiles.index("(security bot,male)"))
        self.assertLess(tiles.index("(blank bot,female)"),
                        tiles.index("(%s,male)" % names[i + 3]))
        self.assertTrue(any("Placer après" in msg for _g, msg in
                            D.validate(dict(a, sym="S_DOG"), game, [])))

    def test_golemhp(self):
        m = T.from_template(0)
        I.install(self.tmp, [m])
        hp = D.read_golemhp(os.path.join(self.tmp, I.MAKEMON_C))
        self.assertEqual(hp[m["bn"]], m["golem_hp"])

    def test_po_entries(self):
        m = T.from_template(4)          # araignée-robot, féminin
        I.install(self.tmp, [m])
        cyber = D.read_po(os.path.join(self.tmp, "po", "themes",
                                       "fr@cyber.po"))
        self.assertEqual(cyber[("monster", m["name"])], m["fr_name"])
        self.assertEqual(cyber[("gender", m["name"])], "f")


def json_copy(m):
    return json.loads(json.dumps(m))


class NoColors:
    def __getattr__(self, name):
        return lambda *a, **k: 0


def bare_editor(monsters=()):
    """Éditeur sans écran, pour essayer sa logique hors de curses."""
    ed = E.Editor.__new__(E.Editor)
    ed.colors = NoColors()
    ed.monsters = [D.normalize(m) for m in monsters]
    ed.cur, ed.field, ed.focus, ed.msg = 0, 1, "list", ""
    ed.modified, ed.undo_stack, ed.redo_stack = False, [], []
    ed._game = []
    ed.project = os.path.join(tempfile.gettempdir(), "nhmonedit-test.json")
    return ed


class TestEditor(unittest.TestCase):
    def test_undo_redo(self):
        ed = bare_editor([T.from_template(0)])
        ed.checkpoint()
        ed.mon()["level"] = 9
        ed.checkpoint()
        ed.mon()["level"] = 12
        ed.undo()
        ed.undo()
        self.assertEqual(ed.mon()["level"], T.from_template(0)["level"])
        ed.undo(redo=True)
        self.assertEqual(ed.mon()["level"], 9)
        ed.undo(redo=True)
        self.assertEqual(ed.mon()["level"], 12)
        ed.undo(redo=True)
        self.assertEqual(ed.msg, "Rien à rétablir")
        # une nouvelle modification efface ce qui pouvait être rétabli
        ed.undo()
        ed.checkpoint()
        ed.mon()["level"] = 3
        ed.undo(redo=True)
        self.assertEqual(ed.mon()["level"], 3)

    def test_compare_lines(self):
        ed = bare_editor()
        a = T.from_template(0)
        b = D.normalize(dict(a))
        lines, ndiff = ed.compare_lines(a, b, 100)
        self.assertEqual(ndiff, 0)
        b = D.normalize(json_copy(a))
        b["level"] += 1
        b["attacks"][0][2] += 1
        lines, ndiff = ed.compare_lines(a, b, 100)
        self.assertEqual(ndiff, 3)          # niveau, attaque, difficulté
        text = [l[0] if isinstance(l, tuple) else l for l in lines]
        diff = [l for l in text if l.startswith("≠")]
        self.assertTrue(any("Niveau" in l for l in diff))
        self.assertTrue(all(len(l) <= 100 for l in text))

    def test_merge_projects(self):
        ed = bare_editor([T.from_template(0), T.from_template(1)])
        with tempfile.TemporaryDirectory() as d:
            other = os.path.join(d, "autre.json")
            mech = T.from_template(7)
            P.write_project(other, [T.from_template(0), mech,
                                    dict(json_copy(mech), level=20)])
            added, same = ed.add_monsters(P.read_monsters(other))
            self.assertEqual((added, same), (2, 1))
            names = [m["name"] for m in ed.monsters]
            self.assertEqual(names[2:], ["combat mech", "combat mech mk II"])
            self.assertTrue(ed.modified)
            with open(other, "w") as f:
                f.write("{}")
            with self.assertRaises(P.ProjectError):
                P.read_monsters(other)

    def test_export_monster(self):
        ed = bare_editor([T.from_template(0)])
        with tempfile.TemporaryDirectory() as d:
            m = T.from_template(5)
            path = P.export_path(d, m)
            self.assertTrue(path.endswith("android.nhmon.json"))
            P.write_monster(path, m)
            self.assertEqual(ed.add_monsters(P.read_monsters(path)), (1, 0))
            self.assertTrue(P.same_monster(ed.mon(), m))
            self.assertEqual(ed.add_monsters(P.read_monsters(path)), (0, 1))

    def test_autosave(self):
        ed = bare_editor([T.from_template(0)])
        with tempfile.TemporaryDirectory() as d:
            ed.project = os.path.join(d, "p.json")
            ed.autosave_delay, ed.autosave_time = 60, 0
            P.write_project(ed.project, ed.monsters)
            ed.autosave()                   # rien à sauver
            self.assertIsNone(P.pending_autosave(ed.project))
            ed.checkpoint()
            ed.mon()["level"] = 30
            ed.autosave()
            auto = P.pending_autosave(ed.project)
            self.assertTrue(auto)
            self.assertEqual(P.read_monsters(auto)[0]["level"], 30)
            # le projet enregistré après : la sauvegarde est périmée
            os.utime(auto, (1, 1))
            self.assertIsNone(P.pending_autosave(ed.project))
            self.assertFalse(os.path.exists(auto))

    def test_personal_templates(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "sous", "modeles.json")
            self.assertEqual(P.read_templates(path), [])
            m = T.from_template(9)
            P.write_templates(path, [("Tourelle Militech", "plafond", m)])
            (name, desc, back), = P.read_templates(path)
            self.assertEqual((name, desc), ("Tourelle Militech", "plafond"))
            self.assertTrue(P.same_monster(back, m))

    def test_config(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "config")
            with open(path, "w") as f:
                f.write("[jeu]\nsources = ~/nh-src\nmake = -j2 "
                        "WANT_WIN_ALL=1\ncouleur = rouge\n"
                        "[editeur]\nprojet = /tmp/robots.json\n"
                        "souris = non\nsauvegarde = 30\nlangue = de\n"
                        "[autre]\n")
            cfg, errs = C.load(path)
            self.assertEqual(cfg["src"], os.path.expanduser("~/nh-src"))
            self.assertEqual(cfg["make"], "-j2 WANT_WIN_ALL=1")
            self.assertEqual((cfg["mouse"], cfg["autosave"]), (False, 30))
            self.assertEqual(len(errs), 3)      # couleur, langue, [autre]
            old = os.environ.pop("NHMONEDIT_SRC", None)
            try:
                self.assertEqual(E.parse_args([], cfg), (
                    "/tmp/robots.json", os.path.expanduser("~/nh-src")))
                self.assertEqual(E.parse_args(["a.json", "--src", "/s"],
                                              cfg)[1], "/s")
            finally:
                if old is not None:
                    os.environ["NHMONEDIT_SRC"] = old

    def test_filter_ignores_accents(self):
        self.assertIn(U.fold("securite"), U.fold("Robot de Sécurité"))
        self.assertEqual(U.fold("araignée-robot"), "araignee-robot")


if __name__ == "__main__":
    unittest.main()
