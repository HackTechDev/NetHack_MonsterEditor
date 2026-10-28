"""Modèles de robots et de mechas pour Night City, et tuiles.

Chaque modèle part de new_monster() et change ce qui le distingue.

La tuile 16x16 ne sert qu'aux interfaces graphiques (Qt, X11), mais
win/share/monsters.txt en demande une par monstre : elle est tirée d'une
silhouette, colorée d'après la couleur du monstre (tile_for()). La
silhouette « auto » dépend de la classe ; « personnalisée » garde la
tuile dessinée à la main (ou importée du jeu).
"""

import copy

import nhmon_data as D
from nhmon_i18n import _

# --- silhouettes (16 lignes de 16 pixels) --------------------------------
SHAPES = {
    "humanoïde": [
        "................",
        "......PPPP......",
        ".....PBBBBP.....",
        ".....PPPPPP.....",
        "......OPPO......",
        "...PPPPPPPPPP...",
        "..POPPBBBBPPOP..",
        "..PO.PBBBBP.OP..",
        "..PO.PPPPPP.OP..",
        "..AA.PPPPPP.AA..",
        ".....PP..PP.....",
        ".....PO..OP.....",
        ".....PO..OP.....",
        ".....PO..OP.....",
        "....APP..PPA....",
        "................",
    ],
    "mecha": [
        "................",
        ".....OOOOOO.....",
        "....OPBBBBPO....",
        "....OPPPPPPO....",
        ".OOOPPPPPPPPOOO.",
        ".OPPPBBPPBBPPPO.",
        ".OPAPPPPPPPPAPO.",
        ".WWAPPPPPPPPAWW.",
        ".WW.PPPHHPPP.WW.",
        "....PPP..PPP....",
        "...OPP....PPO...",
        "...OPP....PPO...",
        "...OPP....PPO...",
        "..AOPPA..APPOA..",
        "..AAAAA..AAAAA..",
        "................",
    ],
    "drone": [
        "................",
        "................",
        ".OOOO......OOOO.",
        "...P........P...",
        "...PPPPPPPPPP...",
        "..PPBBBBBBBBPP..",
        "..PBDDBBBBDDBP..",
        "..PPBBBBBBBBPP..",
        "...PPPPPPPPPP...",
        "....A..PP..A....",
        ".......DD.......",
        "................",
        "................",
        "................",
        "................",
        "................",
    ],
    "sphère": [
        "................",
        "................",
        "......PPPP......",
        "....PPOOOOPP....",
        "...POOBBBBOOP...",
        "...POBDDDDBOP...",
        "..POOBDHHDBOOP..",
        "..POOBDHHDBOOP..",
        "...POBDDDDBOP...",
        "...POOBBBBOOP...",
        "....PPOOOOPP....",
        "......PPPP......",
        "................",
        "................",
        "................",
        "................",
    ],
    "araignée": [
        "................",
        "................",
        "..A..........A..",
        "...P...PP...P...",
        "....P.PPPP.P....",
        ".PP..PPBBPP..PP.",
        "...PPPBDDBPPP...",
        ".....PPPPPP.....",
        "...PPPPPPPPPP...",
        ".PP..PPPPPP..PP.",
        "....P.PPPP.P....",
        "...P........P...",
        "..A..........A..",
        "................",
        "................",
        "................",
    ],
    "chenilles": [
        "................",
        "................",
        "................",
        "......PPPP......",
        ".....PBBBBP.....",
        "..OOOPPPPPPOOOOO",
        ".....PPPPPP.....",
        "...PPPPPPPPPP...",
        "..PPPPBBBBPPPP..",
        "..PPPPPPPPPPPP..",
        ".AAAAAAAAAAAAAA.",
        ".AWAWAWAWAWAWAA.",
        ".AAAAAAAAAAAAAA.",
        "................",
        "................",
        "................",
    ],
}


SHAPE_AUTO = "auto"
SHAPE_CUSTOM = "personnalisée"
# silhouette automatique selon la classe
CLASS_SHAPE = {
    "S_GIANT": "mecha", "S_EYE": "sphère", "S_LIGHT": "sphère",
    "S_VORTEX": "sphère", "S_BAT": "drone", "S_ANT": "drone",
    "S_XAN": "drone", "S_SPIDER": "araignée", "S_RUSTMONST": "chenilles",
    "S_BLOB": "chenilles", "S_PUDDING": "chenilles", "S_JELLY": "chenilles",
    "S_TRAPPER": "chenilles", "S_PIERCER": "chenilles",
}
# couleur CLR_* -> lettre de la palette des tuiles (carrosserie)
COLOR_LETTER = {
    0: "S", 1: "D", 2: "F", 3: "J", 4: "E", 5: "I", 6: "P", 7: "W", 8: "W",
    9: "C", 10: "G", 11: "H", 12: "B", 13: "I", 14: "B", 15: "N",
}


# libellés affichés (les noms français restent ceux du fichier projet)
SHAPE_LABEL = {
    "auto": _("auto"), "personnalisée": _("personnalisée"),
    "humanoïde": _("humanoïde"), "mecha": _("mecha"), "drone": _("drone"),
    "sphère": _("sphère"), "araignée": _("araignée"),
    "chenilles": _("chenilles"),
}


def shape_label(s):
    return SHAPE_LABEL.get(s, s)


def shape_choices():
    return [SHAPE_AUTO] + list(SHAPES) + [SHAPE_CUSTOM]


def shape_of(m):
    """Silhouette effective (jamais « auto »)."""
    s = m.get("tile_shape", SHAPE_AUTO)
    if s == SHAPE_AUTO:
        return CLASS_SHAPE.get(m["sym"], "humanoïde")
    return s


def tile_for(m):
    """Tuile écrite dans monsters.txt pour ce monstre."""
    shape = shape_of(m)
    if shape not in SHAPES:
        return list(m["tile"])
    body = COLOR_LETTER.get(D.COLOR_VALUE.get(m["color"], 6), "P")
    light = "H" if body == "D" else "D"
    return make_tile(shape, body, light)


def make_tile(shape, body="P", light="B"):
    """Tuile d'une silhouette, recolorée : P -> body, B -> light."""
    tr = str.maketrans({"P": body, "B": light})
    return [row.translate(tr) for row in SHAPES[shape]]


def _m(**kw):
    m = D.new_monster()
    atk = kw.pop("attacks", [])
    m["attacks"] = [list(a) for a in atk] + \
        [list(D.NO_ATTK) for _ in range(D.NATTK - len(atk))]
    m["tile_shape"] = kw.pop("shape")
    m.update(kw)
    return m


ROBOT = ["M1_BREATHLESS", "M1_MINDLESS"]

TEMPLATES = [
    (_("Robot de sécurité"), _("humanoïde, matraque électrique, classe golem"),
     _m(bn="SECURITY_BOT", name="security bot",
        fr_name="robot de sécurité", fr_gender="m", sym="S_GOLEM",
        level=6, move=10, ac=4, mr=10, align=0,
        geno=["G_GENO", "G_NOCORPSE"], freq=2,
        attacks=[("AT_WEAP", "AD_PHYS", 1, 8), ("AT_TUCH", "AD_ELEC", 1, 6)],
        weight=900, nutrition=0, sound="MS_SOLDIER", size="MZ_MEDIUM",
        mr1=["MR_ELEC", "MR_SLEEP", "MR_POISON"], mr2=[],
        flags1=ROBOT + ["M1_HUMANOID", "M1_THICK_HIDE"],
        flags2=["M2_HOSTILE", "M2_NEUTER", "M2_COLLECT"],
        flags3=["M3_INFRAVISION"], color="CLR_BRIGHT_BLUE", golem_hp=55,
        shape="humanoïde",
        encyclo_fr="Unité de patrouille standard des corporations. "
        "Programmée pour « désescalader », elle le fait à coups de "
        "matraque à 50 000 volts. Ses mises à jour de sécurité ont "
        "trois ans de retard.",
        encyclo_en="Standard corporate patrol unit. Programmed to "
        "de-escalate, which it does with a 50,000-volt baton.")),
    (_("Drone de surveillance"), _("sphère volante, flash aveuglant"),
     _m(bn="SURVEILLANCE_DRONE", name="surveillance drone",
        fr_name="drone de surveillance", fr_gender="m", sym="S_EYE",
        level=2, move=15, ac=7, mr=0, align=0,
        geno=["G_GENO", "G_NOCORPSE", "G_SGROUP"], freq=2,
        attacks=[("AT_GAZE", "AD_BLND", 1, 4), ("AT_TUCH", "AD_ELEC", 1, 3)],
        weight=40, nutrition=0, sound="MS_BUZZ", size="MZ_TINY",
        mr1=["MR_SLEEP", "MR_POISON"], mr2=[],
        flags1=ROBOT + ["M1_FLY", "M1_NOLIMBS", "M1_NOHEAD", "M1_NOTAKE"],
        flags2=["M2_HOSTILE", "M2_NEUTER", "M2_WANDER"], flags3=[],
        color="CLR_BRIGHT_CYAN",
        shape="sphère",
        encyclo_fr="Petite caméra à rotors qui suit les passants en "
        "bourdonnant. Son projecteur, prévu pour la reconnaissance "
        "faciale, aveugle surtout les visages qu'il reconnaît.",
        encyclo_en="A small rotor-borne camera. Its facial-recognition "
        "floodlight mostly blinds the faces it recognizes.")),
    (_("Drone d'assaut"), _("volant, rotors tranchants, arc électrique"),
     _m(bn="ASSAULT_DRONE", name="assault drone",
        fr_name="drone d'assaut", fr_gender="m", sym="S_BAT",
        level=8, move=20, ac=3, mr=0, align=-3,
        geno=["G_GENO", "G_NOCORPSE"], freq=1,
        attacks=[("AT_BITE", "AD_PHYS", 2, 6), ("AT_BREA", "AD_ELEC", 3, 6)],
        weight=150, nutrition=0, sound="MS_BUZZ", size="MZ_SMALL",
        mr1=["MR_ELEC", "MR_SLEEP", "MR_POISON"], mr2=[],
        flags1=ROBOT + ["M1_FLY", "M1_NOHANDS", "M1_NOTAKE"],
        flags2=["M2_HOSTILE", "M2_NEUTER"], flags3=["M3_INFRAVISION"],
        color="CLR_RED",
        shape="drone",
        encyclo_fr="Quadrirotor militaire armé d'un arc électrique. "
        "Les gangs les volent, les reprogramment et les revendent aux "
        "corporations qui les avaient perdus.",
        encyclo_en="Military quadrotor fitted with an arc projector.")),
    (_("Drone kamikaze"), _("sphère qui explose au contact"),
     _m(bn="KAMIKAZE_DRONE", name="kamikaze drone",
        fr_name="drone kamikaze", fr_gender="m", sym="S_EYE",
        level=6, move=13, ac=4, mr=0, align=0,
        geno=["G_GENO", "G_NOCORPSE"], freq=1,
        attacks=[("AT_EXPL", "AD_FIRE", 4, 6)],
        weight=10, nutrition=0, sound="MS_BUZZ", size="MZ_SMALL",
        mr1=["MR_FIRE", "MR_SLEEP", "MR_POISON"], mr2=[],
        flags1=ROBOT + ["M1_FLY", "M1_NOLIMBS", "M1_NOHEAD", "M1_NOTAKE",
                        "M1_NOEYES"],
        flags2=["M2_HOSTILE", "M2_NEUTER"], flags3=["M3_INFRAVISIBLE"],
        color="CLR_ORANGE",
        shape="sphère",
        encyclo_fr="Une charge thermobarique, quatre hélices et un "
        "logiciel de poursuite. Il ne fait qu'une chose, et une seule "
        "fois.",
        encyclo_en="A thermobaric charge, four propellers and a "
        "tracking chip. It does one thing, once.")),
    (_("Araignée-robot"), _("accrochée au plafond, dard sédatif"),
     _m(bn="SPIDER_BOT", name="spider bot",
        fr_name="araignée-robot", fr_gender="f", sym="S_SPIDER",
        level=5, move=15, ac=3, mr=0, align=0,
        geno=["G_GENO", "G_NOCORPSE", "G_SGROUP"], freq=2,
        attacks=[("AT_STNG", "AD_SLEE", 1, 4), ("AT_BITE", "AD_PHYS", 1, 6)],
        weight=100, nutrition=0, sound="MS_SILENT", size="MZ_SMALL",
        mr1=["MR_SLEEP", "MR_POISON"], mr2=[],
        flags1=ROBOT + ["M1_CLING", "M1_CONCEAL", "M1_NOHANDS",
                        "M1_ANIMAL"],
        flags2=["M2_HOSTILE", "M2_NEUTER"], flags3=["M3_INFRAVISION"],
        color="CLR_GRAY",
        shape="araignée",
        encyclo_fr="Robot de maintenance à huit pattes, détourné en "
        "piège par les fixers : il se cache dans les gaines et pique "
        "au sédatif tout ce qui passe dessous.",
        encyclo_en="Eight-legged maintenance robot repurposed as an "
        "ambush trap.")),
    (_("Androïde"), _("humain synthétique armé, ramasse les objets"),
     _m(bn="ANDROID", name="android",
        fr_name="androïde", fr_gender="m", sym="S_HUMAN",
        level=8, move=12, ac=5, mr=20, align=-2,
        geno=["G_GENO", "G_NOCORPSE"], freq=1,
        attacks=[("AT_WEAP", "AD_PHYS", 2, 6), ("AT_WEAP", "AD_PHYS", 1, 6)],
        weight=1200, nutrition=0, sound="MS_HUMANOID", size="MZ_MEDIUM",
        mr1=["MR_SLEEP", "MR_POISON"], mr2=[],
        flags1=["M1_BREATHLESS", "M1_HUMANOID", "M1_SEE_INVIS"],
        flags2=["M2_HOSTILE", "M2_STRONG", "M2_COLLECT", "M2_MAGIC"],
        flags3=["M3_INFRAVISION"], color="CLR_WHITE",
        shape="humanoïde",
        encyclo_fr="Indiscernable d'un humain, sauf pour un test de "
        "Voight-Kampff ou un détecteur de métaux. Il collectionne les "
        "objets des autres, par curiosité, dit-il.",
        encyclo_en="Indistinguishable from a human, except under a "
        "Voight-Kampff test or a metal detector.")),
    (_("Robot recycleur"), _("dévore le métal, rouille l'armure"),
     _m(bn="RECYCLER_BOT", name="recycler bot",
        fr_name="robot recycleur", fr_gender="m", sym="S_RUSTMONST",
        level=5, move=12, ac=2, mr=0, align=0,
        geno=["G_GENO", "G_NOCORPSE"], freq=2,
        attacks=[("AT_TUCH", "AD_RUST", 0, 0), ("AT_TUCH", "AD_RUST", 0, 0),
                 ("AT_NONE", "AD_RUST", 0, 0)],
        weight=1000, nutrition=0, sound="MS_SILENT", size="MZ_MEDIUM",
        mr1=["MR_SLEEP", "MR_POISON"], mr2=[],
        flags1=ROBOT + ["M1_ANIMAL", "M1_NOHANDS", "M1_METALLIVORE"],
        flags2=["M2_HOSTILE", "M2_NEUTER"], flags3=[],
        color="CLR_BROWN",
        shape="chenilles",
        encyclo_fr="Benne autonome chargée de récupérer la ferraille "
        "des bas-fonds. Elle ne fait pas la différence entre une "
        "épave et une armure portée.",
        encyclo_en="Autonomous scrap collector. It cannot tell wreckage "
        "from worn armor.")),
    (_("Mecha de combat"), _("géant blindé, lance-flammes"),
     _m(bn="COMBAT_MECH", name="combat mech",
        fr_name="mecha de combat", fr_gender="m", sym="S_GIANT",
        level=13, move=9, ac=0, mr=30, align=-5,
        geno=["G_GENO", "G_NOCORPSE"], freq=1,
        attacks=[("AT_WEAP", "AD_PHYS", 3, 8), ("AT_BREA", "AD_FIRE", 4, 6)],
        weight=3000, nutrition=0, sound="MS_SILENT", size="MZ_HUGE",
        mr1=["MR_FIRE", "MR_SLEEP", "MR_POISON"], mr2=[],
        flags1=ROBOT + ["M1_HUMANOID", "M1_THICK_HIDE"],
        flags2=["M2_HOSTILE", "M2_NEUTER", "M2_STRONG", "M2_NASTY",
                "M2_COLLECT"],
        flags3=["M3_INFRAVISION", "M3_INFRAVISIBLE"],
        color="HI_METAL",
        shape="mecha",
        encyclo_fr="Exosquelette de quatre mètres piloté à distance "
        "par un opérateur payé à la mission. Le lance-flammes du bras "
        "gauche était vendu comme « outil de désherbage urbain ».",
        encyclo_en="A four-meter remote-piloted exoframe. The left-arm "
        "flamethrower was sold as an urban weed-control tool.")),
    (_("Mecha titan"), _("boss de fin : canon à plasma, piétine"),
     _m(bn="TITAN_MECH", name="titan mech",
        fr_name="mecha titan", fr_gender="m", sym="S_GIANT",
        level=20, move=8, ac=-4, mr=60, align=-8,
        geno=["G_NOCORPSE", "G_NOHELL"], freq=1,
        attacks=[("AT_WEAP", "AD_PHYS", 4, 10), ("AT_BREA", "AD_ELEC", 6, 6),
                 ("AT_KICK", "AD_PHYS", 3, 10)],
        weight=6000, nutrition=0, sound="MS_SILENT", size="MZ_GIGANTIC",
        mr1=["MR_FIRE", "MR_ELEC", "MR_SLEEP", "MR_POISON", "MR_STONE"],
        mr2=[],
        flags1=ROBOT + ["M1_HUMANOID", "M1_THICK_HIDE", "M1_SEE_INVIS"],
        flags2=["M2_HOSTILE", "M2_NEUTER", "M2_STRONG", "M2_NASTY",
                "M2_ROCKTHROW", "M2_STALK"],
        flags3=["M3_INFRAVISION", "M3_INFRAVISIBLE"],
        color="CLR_BRIGHT_MAGENTA",
        shape="mecha",
        encyclo_fr="Prototype militaire d'Arasaka perdu lors d'un "
        "transfert de données : son pilote automatique protège "
        "toujours un convoi qui n'existe plus.",
        encyclo_en="A lost military prototype whose autopilot still "
        "escorts a convoy that no longer exists.")),
    (_("Tourelle de sécurité"), _("immobile, attend l'intrus, tir de laser"),
     _m(bn="SECURITY_TURRET", name="security turret",
        fr_name="tourelle de sécurité", fr_gender="f", sym="S_GOLEM",
        level=7, move=0, ac=2, mr=20, align=0,
        geno=["G_GENO", "G_NOCORPSE"], freq=1,
        attacks=[("AT_GAZE", "AD_FIRE", 2, 6), ("AT_GAZE", "AD_BLND", 1, 2)],
        weight=1500, nutrition=0, sound="MS_SHRIEK", size="MZ_MEDIUM",
        mr1=["MR_FIRE", "MR_SLEEP", "MR_POISON"], mr2=[],
        flags1=ROBOT + ["M1_NOLIMBS", "M1_NOTAKE", "M1_THICK_HIDE"],
        flags2=["M2_HOSTILE", "M2_NEUTER"],
        flags3=["M3_WAITFORU", "M3_INFRAVISION"], color="CLR_YELLOW",
        golem_hp=70,
        shape="chenilles",
        encyclo_fr="Tourelle laser fixée au plafond des halls "
        "d'entrée. Une sirène, puis un faisceau : la politique "
        "d'accueil de la maison.",
        encyclo_en="A ceiling-mounted laser turret. A siren, then a "
        "beam: the lobby's welcome policy.")),
    (_("Robot vierge"), _("valeurs de départ d'un robot (classe golem)"),
     _m(shape=SHAPE_AUTO)),
]


def template_list():
    return [(name, desc) for name, desc, _m in TEMPLATES]


def from_template(i):
    return copy.deepcopy(TEMPLATES[i][2])
