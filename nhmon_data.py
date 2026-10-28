"""Données de NetHack 5.0 pour l'éditeur de monstres.

Constantes de include/monflag.h, monattk.h, color.h et defsym.h (avec
une description française), modèle d'un monstre, lecture des entrées
MON() de include/monsters.h, calcul de la difficulté (mstrength() de
src/mondata.c), génération du code C et vérification des valeurs.
"""

import copy
import re

NATTK = 6

# --- classes de monstres (defsym.h : MONSYM) ---------------------------
# (S_nom, caractère, description)
CLASSES = [
    ("S_ANT", "a", "fourmi ou insecte"),
    ("S_BLOB", "b", "blob"),
    ("S_COCKATRICE", "c", "cocatrix"),
    ("S_DOG", "d", "chien ou canidé"),
    ("S_EYE", "e", "œil ou sphère (caméras, sondes)"),
    ("S_FELINE", "f", "félin"),
    ("S_GREMLIN", "g", "gremlin"),
    ("S_HUMANOID", "h", "petit humanoïde"),
    ("S_IMP", "i", "diablotin ou démon mineur"),
    ("S_JELLY", "j", "gelée"),
    ("S_KOBOLD", "k", "kobold"),
    ("S_LEPRECHAUN", "l", "leprechaun"),
    ("S_MIMIC", "m", "mimique"),
    ("S_NYMPH", "n", "nymphe"),
    ("S_ORC", "o", "orque"),
    ("S_PIERCER", "p", "perceur"),
    ("S_QUADRUPED", "q", "quadrupède"),
    ("S_RODENT", "r", "rongeur"),
    ("S_SPIDER", "s", "arachnide (araignées mécaniques)"),
    ("S_TRAPPER", "t", "piégeur"),
    ("S_UNICORN", "u", "licorne ou cheval"),
    ("S_VORTEX", "v", "vortex"),
    ("S_WORM", "w", "ver"),
    ("S_XAN", "x", "xan ou insecte fantastique"),
    ("S_LIGHT", "y", "lumière"),
    ("S_ZRUTY", "z", "zruty"),
    ("S_ANGEL", "A", "être angélique"),
    ("S_BAT", "B", "chauve-souris ou oiseau (drones volants)"),
    ("S_CENTAUR", "C", "centaure"),
    ("S_DRAGON", "D", "dragon"),
    ("S_ELEMENTAL", "E", "élémentaire"),
    ("S_FUNGUS", "F", "champignon ou moisissure"),
    ("S_GNOME", "G", "gnome"),
    ("S_GIANT", "H", "humanoïde géant (mechas)"),
    ("S_JABBERWOCK", "J", "jabberwock"),
    ("S_KOP", "K", "Kop"),
    ("S_LICH", "L", "liche"),
    ("S_MUMMY", "M", "momie"),
    ("S_NAGA", "N", "naga"),
    ("S_OGRE", "O", "ogre"),
    ("S_PUDDING", "P", "pudding"),
    ("S_QUANTMECH", "Q", "mécanicien quantique"),
    ("S_RUSTMONST", "R", "monstre de rouille"),
    ("S_SNAKE", "S", "serpent"),
    ("S_TROLL", "T", "troll"),
    ("S_UMBER", "U", "umber hulk"),
    ("S_VAMPIRE", "V", "vampire"),
    ("S_WRAITH", "W", "spectre"),
    ("S_XORN", "X", "xorn"),
    ("S_YETI", "Y", "simiesque"),
    ("S_ZOMBIE", "Z", "zombie"),
    ("S_HUMAN", "@", "humain ou elfe (androïdes)"),
    ("S_GHOST", " ", "fantôme"),
    ("S_GOLEM", "'", "golem (robots : PV fixes)"),
    ("S_DEMON", "&", "démon majeur"),
    ("S_EEL", ";", "monstre marin"),
    ("S_LIZARD", ":", "lézard"),
    ("S_WORM_TAIL", "~", "queue de ver (interne)"),
]
CLASS_CHAR = {s: c for s, c, _ in CLASSES}

# --- attaques (monattk.h) ----------------------------------------------
ATTACK_TYPES = [
    ("AT_NONE", 0, "passive (riposte au contact)"),
    ("AT_CLAW", 1, "griffe / coup de poing"),
    ("AT_BITE", 2, "morsure / mâchoire"),
    ("AT_KICK", 3, "coup de pied"),
    ("AT_BUTT", 4, "coup de tête / bélier"),
    ("AT_TUCH", 5, "contact"),
    ("AT_STNG", 6, "dard / aiguille"),
    ("AT_HUGS", 7, "étreinte (pince broyeuse)"),
    ("AT_SPIT", 10, "crachat (à distance)"),
    ("AT_ENGL", 11, "engloutit"),
    ("AT_BREA", 12, "souffle (lance-flammes, à distance)"),
    ("AT_EXPL", 13, "explose au contact (kamikaze)"),
    ("AT_BOOM", 14, "explose à sa destruction"),
    ("AT_GAZE", 15, "regard (laser optique, à distance)"),
    ("AT_TENT", 16, "tentacules (câbles)"),
    ("AT_WEAP", 254, "arme (avec des mains)"),
    ("AT_MAGC", 255, "sort (piratage)"),
]
DAMAGE_TYPES = [
    ("AD_PHYS", 0, "physique"),
    ("AD_MAGM", 1, "projectiles magiques"),
    ("AD_FIRE", 2, "feu"),
    ("AD_COLD", 3, "froid (cryogénie)"),
    ("AD_SLEE", 4, "sommeil (sédatif)"),
    ("AD_DISN", 5, "désintégration"),
    ("AD_ELEC", 6, "électricité"),
    ("AD_DRST", 7, "poison (draine la force)"),
    ("AD_ACID", 8, "acide"),
    ("AD_SPC1", 9, "spécial 1 (inutilisé)"),
    ("AD_SPC2", 10, "spécial 2 (inutilisé)"),
    ("AD_BLND", 11, "aveugle (flash)"),
    ("AD_STUN", 12, "étourdit"),
    ("AD_SLOW", 13, "ralentit"),
    ("AD_PLYS", 14, "paralyse (taser)"),
    ("AD_DRLI", 15, "draine les niveaux"),
    ("AD_DREN", 16, "draine l'énergie"),
    ("AD_LEGS", 17, "blesse les jambes"),
    ("AD_STON", 18, "pétrifie"),
    ("AD_STCK", 19, "colle (aimant, grappin)"),
    ("AD_SGLD", 20, "vole l'argent"),
    ("AD_SITM", 21, "vole un objet"),
    ("AD_SEDU", 22, "séduit et vole"),
    ("AD_TLPT", 23, "téléporte"),
    ("AD_RUST", 24, "rouille l'armure"),
    ("AD_CONF", 25, "rend confus (brouillage)"),
    ("AD_DGST", 26, "digère"),
    ("AD_HEAL", 27, "soigne (robot médical)"),
    ("AD_WRAP", 28, "enserre (noie)"),
    ("AD_WERE", 29, "lycanthropie"),
    ("AD_DRDX", 30, "draine la dextérité"),
    ("AD_DRCO", 31, "draine la constitution"),
    ("AD_DRIN", 32, "draine l'intelligence"),
    ("AD_DISE", 33, "maladie"),
    ("AD_DCAY", 34, "pourrit l'organique"),
    ("AD_SSEX", 35, "séduction étendue"),
    ("AD_HALU", 36, "hallucinations"),
    ("AD_DETH", 37, "Mort (cavalier)"),
    ("AD_PEST", 38, "Pestilence (cavalier)"),
    ("AD_FAMN", 39, "Famine (cavalier)"),
    ("AD_SLIM", 40, "change en slime"),
    ("AD_ENCH", 41, "désenchante"),
    ("AD_CORR", 42, "corrode l'armure"),
    ("AD_POLY", 43, "polymorphe"),
    ("AD_CLRC", 240, "sort de prêtre au hasard"),
    ("AD_SPEL", 241, "sort de mage au hasard"),
    ("AD_RBRE", 242, "souffle au hasard"),
    ("AD_SAMU", 252, "frappe, vole l'Amulette"),
    ("AD_CURS", 253, "malédiction (gremlin)"),
]
AT_VALUE = {n: v for n, v, _ in ATTACK_TYPES}
AD_VALUE = {n: v for n, v, _ in DAMAGE_TYPES}
AT_DESC = {n: d for n, _, d in ATTACK_TYPES}
AD_DESC = {n: d for n, _, d in DAMAGE_TYPES}
RANGED_AT = ("AT_SPIT", "AT_BREA", "AT_GAZE")
NO_ATTK = ["AT_NONE", "AD_PHYS", 0, 0]

# --- sons, tailles (monflag.h) -----------------------------------------
SOUNDS = [
    ("MS_SILENT", 0, "silencieux"), ("MS_BARK", 1, "aboie"),
    ("MS_MEW", 2, "miaule"), ("MS_ROAR", 3, "rugit"),
    ("MS_BELLOW", 4, "mugit"), ("MS_GROWL", 5, "grogne"),
    ("MS_SQEEK", 6, "couine"), ("MS_SQAWK", 7, "piaille"),
    ("MS_CHIRP", 8, "pépie"), ("MS_HISS", 9, "siffle (vapeur)"),
    ("MS_BUZZ", 10, "bourdonne (rotors)"),
    ("MS_GRUNT", 11, "grogne (langage)"), ("MS_NEIGH", 12, "hennit"),
    ("MS_MOO", 13, "meugle"), ("MS_WAIL", 14, "gémit"),
    ("MS_GURGLE", 15, "gargouille"), ("MS_BURBLE", 16, "glougloute"),
    ("MS_TRUMPET", 17, "barrit"), ("MS_SHRIEK", 18, "hurle (alarme)"),
    ("MS_BONES", 19, "cliquette"), ("MS_LAUGH", 20, "rit"),
    ("MS_MUMBLE", 21, "marmonne"), ("MS_IMITATE", 22, "imite"),
    ("MS_WERE", 23, "lycanthrope"), ("MS_ORC", 24, "brute"),
    ("MS_HUMANOID", 25, "parle (humanoïde)"),
    ("MS_ARREST", 26, "« Halte, police ! »"),
    ("MS_SOLDIER", 27, "soldat"), ("MS_GUARD", 28, "garde"),
    ("MS_DJINNI", 29, "djinn"), ("MS_NURSE", 30, "infirmière"),
    ("MS_SEDUCE", 31, "séduit"), ("MS_VAMPIRE", 32, "vampire"),
    ("MS_BRIBE", 33, "réclame de l'argent"), ("MS_CUSS", 34, "insulte"),
    ("MS_RIDER", 35, "cavalier"), ("MS_LEADER", 36, "chef de quête"),
    ("MS_NEMESIS", 37, "némésis"), ("MS_GUARDIAN", 38, "gardien"),
    ("MS_SELL", 39, "vend"), ("MS_ORACLE", 40, "oracle"),
    ("MS_PRIEST", 41, "prêtre"), ("MS_SPELL", 42, "lanceur de sorts"),
    ("MS_BOAST", 43, "se vante (géant)"), ("MS_GROAN", 44, "geint"),
]
SIZES = [
    ("MZ_TINY", 0, "minuscule (< 60 cm)"),
    ("MZ_SMALL", 1, "petit (60 cm - 1,20 m)"),
    ("MZ_MEDIUM", 2, "moyen (taille humaine)"),
    ("MZ_LARGE", 3, "grand (2 - 3,60 m)"),
    ("MZ_HUGE", 4, "énorme (3,60 - 7,50 m)"),
    ("MZ_GIGANTIC", 7, "gigantesque"),
]
SIZE_ALIAS = {"MZ_HUMAN": "MZ_MEDIUM"}

# --- couleurs (color.h) -------------------------------------------------
# (nom, numéro CLR_*)
COLORS = [
    ("CLR_BLACK", 0), ("CLR_RED", 1), ("CLR_GREEN", 2), ("CLR_BROWN", 3),
    ("CLR_BLUE", 4), ("CLR_MAGENTA", 5), ("CLR_CYAN", 6), ("CLR_GRAY", 7),
    ("CLR_ORANGE", 9), ("CLR_BRIGHT_GREEN", 10), ("CLR_YELLOW", 11),
    ("CLR_BRIGHT_BLUE", 12), ("CLR_BRIGHT_MAGENTA", 13),
    ("CLR_BRIGHT_CYAN", 14), ("CLR_WHITE", 15),
    ("HI_DOMESTIC", 15), ("HI_LORD", 5), ("HI_OVERLORD", 13),
    ("HI_METAL", 6), ("HI_COPPER", 11), ("HI_SILVER", 7), ("HI_GOLD", 11),
    ("HI_LEATHER", 3), ("HI_CLOTH", 3), ("HI_ORGANIC", 3), ("HI_WOOD", 3),
    ("HI_PAPER", 15), ("HI_GLASS", 14), ("HI_MINERAL", 7), ("HI_ZAP", 12),
    ("DRAGON_SILVER", 14),
]
COLOR_VALUE = dict(COLORS)
COLOR_FR = {
    "CLR_BLACK": "noir (bleu foncé)", "CLR_RED": "rouge",
    "CLR_GREEN": "vert", "CLR_BROWN": "brun", "CLR_BLUE": "bleu",
    "CLR_MAGENTA": "magenta", "CLR_CYAN": "cyan", "CLR_GRAY": "gris",
    "CLR_ORANGE": "orange", "CLR_BRIGHT_GREEN": "vert vif",
    "CLR_YELLOW": "jaune", "CLR_BRIGHT_BLUE": "bleu vif",
    "CLR_BRIGHT_MAGENTA": "magenta vif (néon)",
    "CLR_BRIGHT_CYAN": "cyan vif (néon)", "CLR_WHITE": "blanc",
    "HI_DOMESTIC": "domestique (blanc)", "HI_LORD": "seigneur (magenta)",
    "HI_OVERLORD": "suzerain (magenta vif)", "HI_METAL": "métal (cyan)",
    "HI_COPPER": "cuivre (jaune)", "HI_SILVER": "argent (gris)",
    "HI_GOLD": "or (jaune)", "HI_LEATHER": "cuir (brun)",
    "HI_CLOTH": "tissu (brun)", "HI_ORGANIC": "organique (brun)",
    "HI_WOOD": "bois (brun)", "HI_PAPER": "papier (blanc)",
    "HI_GLASS": "verre (cyan vif)", "HI_MINERAL": "minéral (gris)",
    "HI_ZAP": "rayon (bleu vif)", "DRAGON_SILVER": "argent (cyan vif)",
}

# --- poids nommés (weight.h) -------------------------------------------
WEIGHTS = {
    "WT_ETHEREAL": 0, "WT_JELLY": 50, "WT_NYMPH": 600, "WT_ELF": 800,
    "WT_HUMAN": 1450, "WT_BABY_DRAGON": 1500, "WT_DRAGON": 4500,
}

# --- résistances (MR_*), conférées en mangeant le cadavre ---------------
RESISTS = [
    ("MR_FIRE", 0x01, "feu"), ("MR_COLD", 0x02, "froid"),
    ("MR_SLEEP", 0x04, "sommeil"), ("MR_DISINT", 0x08, "désintégration"),
    ("MR_ELEC", 0x10, "électricité"), ("MR_POISON", 0x20, "poison"),
    ("MR_ACID", 0x40, "acide"), ("MR_STONE", 0x80, "pétrification"),
]

# --- génération (G_*) ---------------------------------------------------
GENFLAGS = [
    ("G_UNIQ", 0x1000, "unique (créé une seule fois)"),
    ("G_NOHELL", 0x0800, "jamais dans la Géhenne"),
    ("G_HELL", 0x0400, "seulement dans la Géhenne"),
    ("G_NOGEN", 0x0200, "jamais au hasard (niveaux spéciaux)"),
    ("G_SGROUP", 0x0080, "en petits groupes"),
    ("G_LGROUP", 0x0040, "en grands groupes"),
    ("G_GENO", 0x0020, "peut être génocidé"),
    ("G_NOCORPSE", 0x0010, "ne laisse pas de cadavre (épave)"),
]

# --- drapeaux M1, M2, M3 ------------------------------------------------
FLAGS1 = [
    ("M1_FLY", 0x00000001, "vole ou flotte"),
    ("M1_SWIM", 0x00000002, "traverse l'eau"),
    ("M1_AMORPHOUS", 0x00000004, "passe sous les portes"),
    ("M1_WALLWALK", 0x00000008, "traverse la roche"),
    ("M1_CLING", 0x00000010, "s'accroche au plafond"),
    ("M1_TUNNEL", 0x00000020, "creuse la roche (foreuse)"),
    ("M1_NEEDPICK", 0x00000040, "creuse avec une pioche"),
    ("M1_CONCEAL", 0x00000080, "se cache sous les objets"),
    ("M1_HIDE", 0x00000100, "se camoufle (plafond)"),
    ("M1_AMPHIBIOUS", 0x00000200, "survit sous l'eau"),
    ("M1_BREATHLESS", 0x00000400, "ne respire pas"),
    ("M1_NOTAKE", 0x00000800, "ne ramasse rien"),
    ("M1_NOEYES", 0x00001000, "sans yeux (capteurs)"),
    ("M1_NOHANDS", 0x00002000, "sans mains"),
    ("M1_NOLIMBS", 0x00006000, "sans membres (inclut sans mains)"),
    ("M1_NOHEAD", 0x00008000, "sans tête"),
    ("M1_MINDLESS", 0x00010000, "sans esprit (automate)"),
    ("M1_HUMANOID", 0x00020000, "corps humanoïde"),
    ("M1_ANIMAL", 0x00040000, "corps animal"),
    ("M1_SLITHY", 0x00080000, "corps serpentin"),
    ("M1_UNSOLID", 0x00100000, "sans corps solide (hologramme)"),
    ("M1_THICK_HIDE", 0x00200000, "blindé (peau épaisse)"),
    ("M1_OVIPAROUS", 0x00400000, "pond des œufs"),
    ("M1_REGEN", 0x00800000, "se régénère (nanites)"),
    ("M1_SEE_INVIS", 0x01000000, "voit l'invisible"),
    ("M1_TPORT", 0x02000000, "se téléporte"),
    ("M1_TPORT_CNTRL", 0x04000000, "contrôle la téléportation"),
    ("M1_ACID", 0x08000000, "acide à manger"),
    ("M1_POIS", 0x10000000, "toxique à manger"),
    ("M1_CARNIVORE", 0x20000000, "carnivore"),
    ("M1_HERBIVORE", 0x40000000, "herbivore"),
    ("M1_OMNIVORE", 0x60000000, "omnivore (carnivore + herbivore)"),
    ("M1_METALLIVORE", 0x80000000, "mange le métal (recycleur)"),
]
FLAGS2 = [
    ("M2_NOPOLY", 0x00000001, "le joueur ne peut pas s'y polymorpher"),
    ("M2_UNDEAD", 0x00000002, "mort-vivant"),
    ("M2_WERE", 0x00000004, "lycanthrope"),
    ("M2_HUMAN", 0x00000008, "humain"),
    ("M2_ELF", 0x00000010, "elfe"),
    ("M2_DWARF", 0x00000020, "nain"),
    ("M2_GNOME", 0x00000040, "gnome"),
    ("M2_ORC", 0x00000080, "orque"),
    ("M2_DEMON", 0x00000100, "démon"),
    ("M2_MERC", 0x00000200, "garde ou soldat"),
    ("M2_LORD", 0x00000400, "seigneur de son espèce"),
    ("M2_PRINCE", 0x00000800, "suzerain de son espèce"),
    ("M2_MINION", 0x00001000, "serviteur d'un dieu"),
    ("M2_GIANT", 0x00002000, "géant"),
    ("M2_SHAPESHIFTER", 0x00004000, "change de forme"),
    ("M2_MALE", 0x00010000, "toujours mâle"),
    ("M2_FEMALE", 0x00020000, "toujours femelle"),
    ("M2_NEUTER", 0x00040000, "neutre (ni mâle ni femelle)"),
    ("M2_PNAME", 0x00080000, "nom propre"),
    ("M2_HOSTILE", 0x00100000, "toujours hostile"),
    ("M2_PEACEFUL", 0x00200000, "toujours pacifique"),
    ("M2_DOMESTIC", 0x00400000, "apprivoisable avec de la nourriture"),
    ("M2_WANDER", 0x00800000, "erre au hasard (patrouille)"),
    ("M2_STALK", 0x01000000, "vous suit d'un niveau à l'autre"),
    ("M2_NASTY", 0x02000000, "particulièrement méchant"),
    ("M2_STRONG", 0x04000000, "fort (ou grand)"),
    ("M2_ROCKTHROW", 0x08000000, "lance des rochers"),
    ("M2_GREEDY", 0x10000000, "aime l'or"),
    ("M2_JEWELS", 0x20000000, "aime les gemmes"),
    ("M2_COLLECT", 0x40000000, "ramasse armes et nourriture"),
    ("M2_MAGIC", 0x80000000, "ramasse les objets magiques"),
]
FLAGS3 = [
    ("M3_WANTSAMUL", 0x0001, "veut l'Amulette"),
    ("M3_WANTSBELL", 0x0002, "veut la Cloche"),
    ("M3_WANTSBOOK", 0x0004, "veut le Livre"),
    ("M3_WANTSCAND", 0x0008, "veut le Candélabre"),
    ("M3_WANTSARTI", 0x0010, "veut l'artefact de quête"),
    ("M3_WANTSALL", 0x001f, "veut tous les objets majeurs"),
    ("M3_COVETOUS", 0x001f, "convoite (= M3_WANTSALL)"),
    ("M3_WAITFORU", 0x0040, "attend de vous voir (sentinelle)"),
    ("M3_CLOSE", 0x0080, "vous laisse approcher"),
    ("M3_INFRAVISION", 0x0100, "infravision (capteur thermique)"),
    ("M3_INFRAVISIBLE", 0x0200, "visible en infravision (chaud)"),
    ("M3_DISPLACES", 0x0400, "écarte les monstres de son chemin"),
]
FLAG_TABLES = {"mr1": RESISTS, "mr2": RESISTS, "geno": GENFLAGS,
               "flags1": FLAGS1, "flags2": FLAGS2, "flags3": FLAGS3}
FLAG_VALUE = {}
for _tab in (RESISTS, GENFLAGS, FLAGS1, FLAGS2, FLAGS3):
    FLAG_VALUE.update({n: v for n, v, _ in _tab})

ALIGN_NONE = -128   # A_NONE

# --- palette des tuiles (win/share/monsters.txt) ------------------------
TILE_PALETTE = [
    (".", (71, 108, 108)), ("A", (0, 0, 0)), ("B", (0, 182, 255)),
    ("C", (255, 108, 0)), ("D", (255, 0, 0)), ("E", (0, 0, 255)),
    ("F", (0, 145, 0)), ("G", (108, 255, 0)), ("H", (255, 255, 0)),
    ("I", (255, 0, 255)), ("J", (145, 71, 0)), ("K", (204, 79, 0)),
    ("L", (255, 182, 145)), ("M", (237, 237, 237)),
    ("N", (255, 255, 255)), ("O", (215, 215, 215)),
    ("P", (108, 145, 182)), ("Q", (18, 18, 18)), ("R", (54, 54, 54)),
    ("S", (73, 73, 73)), ("T", (82, 82, 82)), ("U", (205, 205, 205)),
    ("V", (104, 104, 104)), ("W", (131, 131, 131)),
    ("X", (140, 140, 140)), ("Y", (149, 149, 149)),
    ("Z", (195, 195, 195)), ("0", (100, 100, 100)),
    ("1", (72, 108, 108)),
]
TILE_SIZE = 16


# --- modèle -------------------------------------------------------------

def blank_tile():
    return ["." * TILE_SIZE for _ in range(TILE_SIZE)]


def new_monster():
    """Un monstre vide, avec des valeurs raisonnables pour un robot."""
    return {
        "bn": "NEW_ROBOT",
        "name": "new robot",
        "name_m": "", "name_f": "",          # NAMS(mâle, femelle, neutre)
        "fr_name": "nouveau robot", "fr_gender": "m",
        "fr_name_m": "", "fr_name_f": "",
        "sym": "S_GOLEM",
        "level": 5, "move": 9, "ac": 5, "mr": 0, "align": 0,
        "geno": ["G_GENO", "G_NOCORPSE"], "freq": 1,
        "attacks": [["AT_CLAW", "AD_PHYS", 1, 6]]
                   + [list(NO_ATTK) for _ in range(NATTK - 1)],
        "weight": 1000, "nutrition": 0,
        "sound": "MS_SILENT", "size": "MZ_MEDIUM",
        "mr1": ["MR_SLEEP", "MR_POISON"], "mr2": [],
        "flags1": ["M1_BREATHLESS", "M1_MINDLESS", "M1_HUMANOID"],
        "flags2": ["M2_HOSTILE", "M2_NEUTER"],
        "flags3": [],
        "difficulty": None,            # None : calculée
        "color": "HI_METAL",
        "golem_hp": 50,                # PV fixes des golems (S_GOLEM)
        "tile_shape": "auto",          # silhouette de la tuile
        "tile": blank_tile(),          # tuile dessinée (« personnalisée »)
        "encyclo_en": "", "encyclo_fr": "",
        "notes": "",
    }


def normalize(m):
    """Complète un monstre lu d'un fichier (anciens champs absents)."""
    if "tile_shape" not in m:
        # projet d'avant les silhouettes : on garde la tuile dessinée
        drawn = any(c != "." for row in m.get("tile", []) for c in row)
        m["tile_shape"] = "personnalisée" if drawn else "auto"
    base = new_monster()
    for k, v in base.items():
        if k not in m:
            m[k] = copy.deepcopy(v)
    atk = [list(a) for a in m["attacks"]][:NATTK]
    while len(atk) < NATTK:
        atk.append(list(NO_ATTK))
    m["attacks"] = atk
    if len(m["tile"]) != TILE_SIZE:
        m["tile"] = blank_tile()
    return m


def attacks_used(m):
    return [a for a in m["attacks"] if a[0] != "AT_NONE" or a[1] != "AD_PHYS"
            or a[2] or a[3]]


def flag_mask(names):
    v = 0
    for n in names:
        v |= FLAG_VALUE.get(n, 0)
    return v


def has_flag(m, field, name):
    """Vrai si le drapeau est donné, directement ou par un masque plus
    large (M1_NOLIMBS contient M1_NOHANDS)."""
    return flag_mask(m[field]) & FLAG_VALUE[name] == FLAG_VALUE[name]


def geno_value(m):
    return flag_mask(m["geno"]) | (m["freq"] & 7)


# --- difficulté : mstrength() de src/mondata.c ---------------------------

def mstrength(m):
    tmp = m["level"]
    if tmp > 49:
        tmp = 2 * (tmp - 6) // 4
    geno = geno_value(m)
    n = int(bool(geno & 0x80))
    n += int(bool(geno & 0x40)) << 1
    # attaque à distance (mstrength_ranged_attk)
    for at, ad, dn, dd in m["attacks"]:
        j = AT_VALUE[at]
        if j >= AT_VALUE["AT_WEAP"] or at in RANGED_AT:
            n += 1
            break
    n += m["ac"] < 4
    n += m["ac"] < 0
    n += m["move"] >= 18
    strong = has_flag(m, "flags2", "M2_STRONG")
    for at, ad, dn, dd in m["attacks"]:
        t = AT_VALUE[at]
        n += t > 0
        n += at == "AT_MAGC"
        n += at == "AT_WEAP" and strong
        if at == "AT_EXPL":
            n += 3 if ad in ("AD_COLD", "AD_FIRE") else \
                5 if ad == "AD_ELEC" else 0
    for at, ad, dn, dd in m["attacks"]:
        if ad in ("AD_DRLI", "AD_STON", "AD_DRST", "AD_DRDX", "AD_DRCO",
                  "AD_WERE"):
            n += 2
        elif m["name"] != "grid bug":
            n += ad != "AD_PHYS"
        n += dn * dd > 23
    if m["name"] == "leprechaun":
        n -= 2
    if m["name"] in ("killer bee", "soldier ant"):
        n += 2
    if n == 0:
        tmp -= 1
    elif n < 6:
        tmp += n // 3 + 1
    else:
        tmp += n // 2
    return max(tmp, 0)


def difficulty(m):
    return mstrength(m) if m["difficulty"] is None else m["difficulty"]


def max_damage(m):
    return sum(a[2] * a[3] for a in attacks_used(m)
               if a[0] not in ("AT_NONE", "AT_BOOM"))


# --- génération du code C -----------------------------------------------

def c_string(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _flags_expr(names):
    return " | ".join(names) if names else "0"


def nam_expr(m):
    if m["name_m"] and m["name_f"]:
        return "NAMS(%s, %s, %s)" % (c_string(m["name_m"]),
                                     c_string(m["name_f"]),
                                     c_string(m["name"]))
    return "NAM(%s)" % c_string(m["name"])


def _wrap(items, first, indent, width=78, last=","):
    """Range des morceaux sur des lignes de largeur limitée, comme dans
    monsters.h. Un morceau trop long (liste de drapeaux) est coupé sur
    ses « | », la suite indentée de quatre espaces de plus."""
    lines, cur, fresh = [], first, True
    for i, it in enumerate(items):
        p = it + ("," if i < len(items) - 1 else last)
        sep = "" if fresh else " "
        if len(cur + sep + p) <= width:
            cur, fresh = cur + sep + p, False
            continue
        if not fresh:
            lines.append(cur)
            cur, sep = indent, ""
        if len(cur + p) <= width or " | " not in p:
            cur, fresh = cur + p, False
            continue
        parts = p.split(" | ")
        cur += parts[0]
        for q in parts[1:]:
            if len(cur + " | " + q) <= width:
                cur += " | " + q
            else:
                lines.append(cur)
                cur = indent + "    | " + q
        fresh = False
    if not fresh:
        lines.append(cur)
    return lines


def c_entry(m, marker=True):
    """Entrée MON() du monstre, au format de include/monsters.h."""
    i8 = " " * 8
    geno = list(m["geno"])
    if m["freq"] or not geno:
        geno.append(str(m["freq"]))
    attacks = []
    for at, ad, dn, dd in m["attacks"]:
        if at == "AT_NONE" and ad == "AD_PHYS" and not dn and not dd:
            attacks.append("NO_ATTK")
        else:
            attacks.append("ATTK(%s, %s, %d, %d)" % (at, ad, dn, dd))
    align = "A_NONE" if m["align"] == ALIGN_NONE else str(m["align"])
    out = []
    if marker:
        out.append("    /* nhmonedit: %s */" % m["bn"])
    out.append("    MON(%s, %s," % (nam_expr(m), m["sym"]))
    out += _wrap(["LVL(%d, %d, %d, %d, %s)" % (m["level"], m["move"],
                                               m["ac"], m["mr"], align),
                  "(%s)" % " | ".join(geno)], i8, i8)
    # attaques : A(a1, a2, ... a6),
    out += _wrap(attacks, i8 + "A(", i8 + "  ", last="),")
    out += _wrap(["SIZ(%d, %d, %s, %s)" % (m["weight"], m["nutrition"],
                                          m["sound"], m["size"]),
                  _flags_expr(m["mr1"]), _flags_expr(m["mr2"])],
                 i8, i8)
    out += _wrap([_flags_expr(m["flags1"]), _flags_expr(m["flags2"]),
                  _flags_expr(m["flags3"])], i8, i8)
    out.append(i8 + "%d, %s, %s)," % (difficulty(m), m["color"], m["bn"]))
    return "\n".join(out)


# --- lecture de include/monsters.h ---------------------------------------

def _strip_comments(text):
    """Remplace les commentaires par des blancs (positions conservées)."""
    return re.sub(r"/\*.*?\*/",
                  lambda mo: re.sub(r"[^\n]", " ", mo.group(0)),
                  text, flags=re.S)


def _active_lines(text):
    """Efface les blocs #if 0 et #ifdef (options non définies) et les
    directives, en gardant la longueur des lignes (positions conservées)."""
    out, stack = [], []
    for line in text.split("\n"):
        s = line.strip()
        if s.startswith("#if"):
            off = s.startswith("#if 0") or s.startswith("#ifdef") or \
                s.startswith("#if defined")
            stack.append(off)
            out.append(" " * len(line))
            continue
        if s.startswith("#else"):
            if stack:
                stack[-1] = not stack[-1]
            out.append(" " * len(line))
            continue
        if s.startswith("#endif"):
            if stack:
                stack.pop()
            out.append(" " * len(line))
            continue
        if s.startswith("#"):
            out.append(" " * len(line))
            continue
        out.append(" " * len(line) if any(stack) else line)
    return "\n".join(out)


def split_args(s):
    """Coupe s sur les virgules hors parenthèses et chaînes."""
    args, depth, cur, instr = [], 0, [], False
    i = 0
    while i < len(s):
        c = s[i]
        if instr:
            cur.append(c)
            if c == "\\":
                cur.append(s[i + 1])
                i += 1
            elif c == '"':
                instr = False
        elif c == '"':
            instr = True
            cur.append(c)
        elif c == "(":
            depth += 1
            cur.append(c)
        elif c == ")":
            depth -= 1
            cur.append(c)
        elif c == "," and depth == 0:
            args.append("".join(cur).strip())
            cur = []
        else:
            cur.append(c)
        i += 1
    if "".join(cur).strip():
        args.append("".join(cur).strip())
    return args


def _inner(expr, name):
    expr = expr.strip()
    if not expr.startswith(name + "(") or not expr.endswith(")"):
        raise ValueError("%s attendu : %s" % (name, expr[:40]))
    return expr[len(name) + 1:-1]


def _int(tok):
    tok = tok.strip().strip("()").strip()
    if tok in WEIGHTS:
        return WEIGHTS[tok]
    if tok == "A_NONE":
        return ALIGN_NONE
    return int(tok, 0)


def _flags(expr):
    expr = expr.strip()
    while expr.startswith("(") and expr.endswith(")"):
        expr = expr[1:-1].strip()
    names, num = [], 0
    for t in expr.split("|"):
        t = t.strip().strip("()").strip()
        if not t or t in ("0", "0L"):
            continue
        if re.match(r"^\d+L?$", t):
            num |= int(t.rstrip("L"))
        else:
            names.append(t)
    return names, num


def _unstr(tok):
    tok = tok.strip()
    return bytes(tok[1:-1], "utf-8").decode("unicode_escape") \
        if tok.startswith('"') else tok


# macros d'attaques définies dans monsters.h (démon séducteur)
ATTACK_MACROS = {
    "SEDUCTION_ATTACKS_YES":
        "A(ATTK(AT_BITE, AD_SSEX, 0, 0), ATTK(AT_CLAW, AD_PHYS, 1, 3), "
        "ATTK(AT_CLAW, AD_PHYS, 1, 3), NO_ATTK, NO_ATTK, NO_ATTK)",
    "SEDUCTION_ATTACKS_NO":
        "A(ATTK(AT_CLAW, AD_PHYS, 1, 3), ATTK(AT_CLAW, AD_PHYS, 1, 3), "
        "ATTK(AT_BITE, AD_DRLI, 2, 6), NO_ATTK, NO_ATTK, NO_ATTK)",
}


def parse_mon(args):
    """Monstre (dict) d'après les 14 arguments d'un MON()."""
    if len(args) != 14:
        raise ValueError("MON() à %d arguments" % len(args))
    m = new_monster()
    nam = args[0]
    if nam.startswith("NAMS("):
        mm, ff, nn = [_unstr(x) for x in split_args(_inner(nam, "NAMS"))]
        m["name_m"], m["name_f"], m["name"] = mm, ff, nn
    else:
        m["name"] = _unstr(_inner(nam, "NAM"))
    m["sym"] = args[1]
    lvl = [_int(x) for x in split_args(_inner(args[2], "LVL"))]
    m["level"], m["move"], m["ac"], m["mr"], m["align"] = lvl
    names, num = _flags(args[3])
    m["geno"], m["freq"] = names, num & 7
    atks = split_args(_inner(ATTACK_MACROS.get(args[4], args[4]), "A"))
    m["attacks"] = []
    for a in atks:
        if a == "NO_ATTK":
            m["attacks"].append(list(NO_ATTK))
        else:
            at, ad, dn, dd = split_args(_inner(a, "ATTK"))
            m["attacks"].append([at, ad, int(dn), int(dd)])
    siz = split_args(_inner(args[5], "SIZ"))
    m["weight"], m["nutrition"] = _int(siz[0]), _int(siz[1])
    m["sound"] = siz[2]
    m["size"] = SIZE_ALIAS.get(siz[3], siz[3])
    m["mr1"] = _flags(args[6])[0]
    m["mr2"] = _flags(args[7])[0]
    m["flags1"] = _flags(args[8])[0]
    m["flags2"] = _flags(args[9])[0]
    m["flags3"] = _flags(args[10])[0]
    m["difficulty"] = _int(args[11])
    m["color"] = args[12]
    m["bn"] = args[13]
    m["fr_name"] = ""
    m["tile"] = blank_tile()
    return m


def iter_mon_calls(text):
    """(début, fin, arguments) de chaque MON() actif d'un texte C."""
    clean = _active_lines(_strip_comments(text))
    # les définitions de macros du début (#define MON(...)) sont retirées
    for mo in re.finditer(r"\bMON\(", clean):
        start = mo.start()
        depth, i, instr = 0, mo.end() - 1, False
        while i < len(clean):
            c = clean[i]
            if instr:
                if c == "\\":
                    i += 1
                elif c == '"':
                    instr = False
            elif c == '"':
                instr = True
            elif c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        yield start, i + 1, split_args(clean[mo.end():i])


def parse_monsters_h(path):
    """Liste des monstres du jeu, dans l'ordre de mons[]."""
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    out = []
    for _s, _e, args in iter_mon_calls(text):
        if len(args) == 14 and args[0].startswith("NAM"):
            out.append(parse_mon(args))
    return out


# --- vérification -------------------------------------------------------

BN_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")


def validate(m, game=None, project=None):
    """Liste de (gravité, message) ; gravité « erreur » ou « attention ».
    game : monstres du jeu (hors ceux de l'éditeur), project : les autres
    monstres du projet."""
    out = []

    def err(msg):
        out.append(("erreur", msg))

    def warn(msg):
        out.append(("attention", msg))

    if not BN_RE.match(m["bn"]):
        err("Identifiant PM_ invalide : majuscules, chiffres et _")
    if not m["name"].strip():
        err("Nom anglais vide")
    elif m["name"] != m["name"].strip() or re.search(r'["(),\\]', m["name"]):
        err("Nom anglais : pas d'espace au bord, ni guillemet, "
            "parenthèse, virgule ou barre oblique inverse")
    if bool(m["name_m"]) != bool(m["name_f"]):
        err("Noms par genre : il faut le masculin ET le féminin")
    others = list(game or []) + list(project or [])
    names = {m["name"], m["name_m"], m["name_f"]} - {""}
    for o in others:
        if o["bn"] == m["bn"]:
            err("Identifiant PM_%s déjà utilisé (%s)" % (m["bn"], o["name"]))
        onames = {o["name"], o["name_m"], o["name_f"]} - {""}
        for n in names & onames:
            err("Nom « %s » déjà utilisé" % n)
    if m["sym"] not in CLASS_CHAR:
        err("Classe inconnue : %s" % m["sym"])
    for key, lo, hi, label in (
            ("level", 0, 49, "Niveau"), ("move", 0, 127, "Vitesse"),
            ("ac", -128, 127, "Classe d'armure"),
            ("mr", 0, 127, "Résistance à la magie"),
            ("align", -128, 127, "Alignement"),
            ("weight", 0, 65535, "Poids"),
            ("nutrition", 0, 65535, "Nutrition"),
            ("freq", 0, 7, "Fréquence")):
        if not lo <= m[key] <= hi:
            err("%s hors limites (%d..%d)" % (label, lo, hi))
    d = difficulty(m)
    if not 0 <= d <= 255:
        err("Difficulté hors limites (0..255)")
    if m["difficulty"] is not None and m["difficulty"] != mstrength(m):
        warn("Difficulté manuelle %d, calculée %d"
             % (m["difficulty"], mstrength(m)))
    for i, (at, ad, dn, dd) in enumerate(m["attacks"]):
        if at not in AT_VALUE:
            err("Attaque %d : type %s inconnu" % (i + 1, at))
        if ad not in AD_VALUE:
            err("Attaque %d : dégât %s inconnu" % (i + 1, ad))
        if not (0 <= dn <= 255 and 0 <= dd <= 255):
            err("Attaque %d : dés hors limites (0..255)" % (i + 1))
        if at == "AT_WEAP" and has_flag(m, "flags1", "M1_NOHANDS"):
            warn("Attaque %d : arme sans mains (M1_NOHANDS)" % (i + 1))
        if ad in ("AD_DETH", "AD_PEST", "AD_FAMN"):
            warn("Attaque %d : dégât réservé aux Cavaliers" % (i + 1))
        if at == "AT_ENGL" and m["size"] in ("MZ_TINY", "MZ_SMALL"):
            warn("Attaque %d : engloutir demande une grande taille"
                 % (i + 1))
    used = attacks_used(m)
    if m["attacks"][:len(used)] != used:
        warn("Attaques : un emplacement vide avant une attaque "
             "(le jeu s'arrête au premier vide pour certaines actions)")
    if not used:
        warn("Aucune attaque")
    if m["sym"] == "S_GOLEM":
        if m["golem_hp"] <= 0:
            err("Classe golem : PV fixes obligatoires (sinon 0 PV)")
        if m["level"] <= 0:
            err("Classe golem : niveau au moins 1 (PV par niveau)")
    if m["sound"] not in [s for s, _, _ in SOUNDS]:
        err("Son inconnu : %s" % m["sound"])
    if m["size"] not in [s for s, _, _ in SIZES]:
        err("Taille inconnue : %s" % m["size"])
    if m["color"] not in COLOR_VALUE:
        err("Couleur inconnue : %s" % m["color"])
    for field in ("mr1", "mr2", "geno", "flags1", "flags2", "flags3"):
        for n in m[field]:
            if n not in FLAG_VALUE:
                err("Drapeau inconnu : %s" % n)
    f2 = m["flags2"]
    if "M2_HOSTILE" in f2 and "M2_PEACEFUL" in f2:
        err("À la fois hostile et pacifique")
    sexes = [x for x in ("M2_MALE", "M2_FEMALE", "M2_NEUTER") if x in f2]
    if len(sexes) > 1:
        err("Plusieurs sexes : %s" % ", ".join(sexes))
    if "G_HELL" in m["geno"] and "G_NOHELL" in m["geno"]:
        err("G_HELL et G_NOHELL à la fois")
    if "G_NOGEN" not in m["geno"] and "G_UNIQ" not in m["geno"] \
            and m["freq"] == 0:
        warn("Fréquence 0 : jamais créé au hasard (ajoutez G_NOGEN)")
    if "G_NOCORPSE" not in m["geno"] and m["nutrition"] == 0:
        warn("Laisse un cadavre de valeur nutritive nulle "
             "(G_NOCORPSE pour une épave de robot)")
    if m["fr_name"][:1].isupper() and not has_flag(m, "flags2", "M2_PNAME"):
        warn("Nom français avec majuscule : il restera ainsi au milieu "
             "des phrases (« le Mecha… ») ; M2_PNAME pour un nom propre")
    if not m["fr_name"].strip():
        warn("Pas de nom français : le jeu affichera le nom anglais")
    if m["fr_gender"] not in ("m", "f"):
        err("Genre français : m ou f")
    if m["name_m"] and not (m["fr_name_m"] and m["fr_name_f"]):
        warn("Noms par genre sans leur traduction française")
    if m["tile_shape"] == "personnalisée" and \
            not any(c != "." for row in m["tile"] for c in row):
        warn("Tuile personnalisée vide (interfaces graphiques seulement)")
    return out


# --- noms français (catalogues .po) --------------------------------------

def _po_unquote(s):
    s = s.strip()
    if not (s.startswith('"') and s.endswith('"')):
        return ""
    return bytes(s[1:-1], "utf-8").decode("unicode_escape").encode(
        "latin-1").decode("utf-8", errors="replace")


def read_po(path, contexts=("monster", "gender")):
    """{(msgctxt, msgid): msgstr} des contextes demandés d'un .po."""
    out = {}
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.read().split("\n")
    except OSError:
        return out
    cur, field = {}, None

    def flush():
        if cur.get("msgctxt") in contexts and "msgid" in cur:
            out[(cur["msgctxt"], cur["msgid"])] = cur.get("msgstr", "")

    for line in lines:
        s = line.strip()
        if not s:
            flush()
            cur, field = {}, None
        elif s.startswith("#"):
            continue
        elif s.startswith('"') and field:
            cur[field] += _po_unquote(s)
        else:
            key, _, rest = s.partition(" ")
            if key in ("msgctxt", "msgid", "msgstr"):
                if key == "msgctxt" and "msgid" in cur:
                    flush()
                    cur = {}
                field = key
                cur[key] = _po_unquote(rest)
            else:
                field = None
    flush()
    return out


def french_names(src):
    """{nom anglais: (nom français, genre)} : le thème fr@cyber passe
    avant fr.po, comme dans le jeu."""
    import os
    po = read_po(os.path.join(src, "po", "fr.po"))
    po.update({k: v for k, v in read_po(
        os.path.join(src, "po", "themes", "fr@cyber.po")).items() if v})
    out = {}
    for (ctx, en), fr in po.items():
        if ctx == "monster" and fr:
            g = po.get(("gender", en), "") or "m"
            out[en] = (fr, g)
    return out


def read_golemhp(path):
    """{PM_ identifiant sans PM_: PV} d'après golemhp() de makemon.c."""
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return {}
    mo = re.search(r"^golemhp\(int type\)\n\{(.*?)^\}", text, re.M | re.S)
    if not mo:
        return {}
    out = {}
    for c in re.finditer(r"case PM_(\w+):[^\n]*\n\s*return (\d+);",
                         mo.group(1)):
        out[c.group(1)] = int(c.group(2))
    return out


def derive_bn(name):
    """Identifiant PM_ d'après un nom : « combat mech » -> COMBAT_MECH."""
    import unicodedata
    s = unicodedata.normalize("NFKD", name)
    s = "".join(c for c in s if ord(c) < 128).upper()
    s = re.sub(r"[^A-Z0-9]+", "_", s).strip("_")
    if s and s[0].isdigit():
        s = "M_" + s
    return s or "NEW_ROBOT"
