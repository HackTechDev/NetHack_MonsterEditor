"""Tests de nhmonedit : lecture de monsters.h, difficulté, code C et
intégration dans une copie des sources.

python3 -m unittest discover -s tests   (depuis le dossier de l'éditeur)
Les sources sont cherchées dans ../NetHack-5.0.0 ou $NHMONEDIT_SRC.
"""

import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import nhmon_data as D  # noqa: E402
import nhmon_install as I  # noqa: E402
import nhmon_templates as T  # noqa: E402

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


if __name__ == "__main__":
    unittest.main()
