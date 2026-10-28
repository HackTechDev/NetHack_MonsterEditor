"""Données de NetHack 5.0 pour l'éditeur de monstres.

Constantes de include/monflag.h, monattk.h, color.h et defsym.h (avec
une description française), modèle d'un monstre, lecture des entrées
MON() de include/monsters.h, calcul de la difficulté (mstrength() de
src/mondata.c), génération du code C et vérification des valeurs.
"""

import copy
import re

from nhmon_i18n import LANG, _

NATTK = 6

# --- classes de monstres (defsym.h : MONSYM) ---------------------------
# (S_nom, caractère, description)
CLASSES = [
    ("S_ANT", "a", _("fourmi ou insecte")),
    ("S_BLOB", "b", _("blob")),
    ("S_COCKATRICE", "c", _("cocatrix")),
    ("S_DOG", "d", _("chien ou canidé")),
    ("S_EYE", "e", _("œil ou sphère (caméras, sondes)")),
    ("S_FELINE", "f", _("félin")),
    ("S_GREMLIN", "g", _("gremlin")),
    ("S_HUMANOID", "h", _("petit humanoïde")),
    ("S_IMP", "i", _("diablotin ou démon mineur")),
    ("S_JELLY", "j", _("gelée")),
    ("S_KOBOLD", "k", _("kobold")),
    ("S_LEPRECHAUN", "l", _("leprechaun")),
    ("S_MIMIC", "m", _("mimique")),
    ("S_NYMPH", "n", _("nymphe")),
    ("S_ORC", "o", _("orque")),
    ("S_PIERCER", "p", _("perceur")),
    ("S_QUADRUPED", "q", _("quadrupède")),
    ("S_RODENT", "r", _("rongeur")),
    ("S_SPIDER", "s", _("arachnide (araignées mécaniques)")),
    ("S_TRAPPER", "t", _("piégeur")),
    ("S_UNICORN", "u", _("licorne ou cheval")),
    ("S_VORTEX", "v", _("vortex")),
    ("S_WORM", "w", _("ver")),
    ("S_XAN", "x", _("xan ou insecte fantastique")),
    ("S_LIGHT", "y", _("lumière")),
    ("S_ZRUTY", "z", _("zruty")),
    ("S_ANGEL", "A", _("être angélique")),
    ("S_BAT", "B", _("chauve-souris ou oiseau (drones volants)")),
    ("S_CENTAUR", "C", _("centaure")),
    ("S_DRAGON", "D", _("dragon")),
    ("S_ELEMENTAL", "E", _("élémentaire")),
    ("S_FUNGUS", "F", _("champignon ou moisissure")),
    ("S_GNOME", "G", _("gnome")),
    ("S_GIANT", "H", _("humanoïde géant (mechas)")),
    ("S_JABBERWOCK", "J", _("jabberwock")),
    ("S_KOP", "K", _("Kop")),
    ("S_LICH", "L", _("liche")),
    ("S_MUMMY", "M", _("momie")),
    ("S_NAGA", "N", _("naga")),
    ("S_OGRE", "O", _("ogre")),
    ("S_PUDDING", "P", _("pudding")),
    ("S_QUANTMECH", "Q", _("mécanicien quantique")),
    ("S_RUSTMONST", "R", _("monstre de rouille")),
    ("S_SNAKE", "S", _("serpent")),
    ("S_TROLL", "T", _("troll")),
    ("S_UMBER", "U", _("umber hulk")),
    ("S_VAMPIRE", "V", _("vampire")),
    ("S_WRAITH", "W", _("spectre")),
    ("S_XORN", "X", _("xorn")),
    ("S_YETI", "Y", _("simiesque")),
    ("S_ZOMBIE", "Z", _("zombie")),
    ("S_HUMAN", "@", _("humain ou elfe (androïdes)")),
    ("S_GHOST", " ", _("fantôme")),
    ("S_GOLEM", "'", _("golem (robots : PV fixes)")),
    ("S_DEMON", "&", _("démon majeur")),
    ("S_EEL", ";", _("monstre marin")),
    ("S_LIZARD", ":", _("lézard")),
    ("S_WORM_TAIL", "~", _("queue de ver (interne)")),
]
CLASS_CHAR = {s: c for s, c, _ in CLASSES}

# --- attaques (monattk.h) ----------------------------------------------
ATTACK_TYPES = [
    ("AT_NONE", 0, _("passive (riposte au contact)")),
    ("AT_CLAW", 1, _("griffe / coup de poing")),
    ("AT_BITE", 2, _("morsure / mâchoire")),
    ("AT_KICK", 3, _("coup de pied")),
    ("AT_BUTT", 4, _("coup de tête / bélier")),
    ("AT_TUCH", 5, _("contact")),
    ("AT_STNG", 6, _("dard / aiguille")),
    ("AT_HUGS", 7, _("étreinte (pince broyeuse)")),
    ("AT_SPIT", 10, _("crachat (à distance)")),
    ("AT_ENGL", 11, _("engloutit")),
    ("AT_BREA", 12, _("souffle (lance-flammes, à distance)")),
    ("AT_EXPL", 13, _("explose au contact (kamikaze)")),
    ("AT_BOOM", 14, _("explose à sa destruction")),
    ("AT_GAZE", 15, _("regard (laser optique, à distance)")),
    ("AT_TENT", 16, _("tentacules (câbles)")),
    ("AT_WEAP", 254, _("arme (avec des mains)")),
    ("AT_MAGC", 255, _("sort (piratage)")),
]
DAMAGE_TYPES = [
    ("AD_PHYS", 0, _("physique")),
    ("AD_MAGM", 1, _("projectiles magiques")),
    ("AD_FIRE", 2, _("feu")),
    ("AD_COLD", 3, _("froid (cryogénie)")),
    ("AD_SLEE", 4, _("sommeil (sédatif)")),
    ("AD_DISN", 5, _("désintégration")),
    ("AD_ELEC", 6, _("électricité")),
    ("AD_DRST", 7, _("poison (draine la force)")),
    ("AD_ACID", 8, _("acide")),
    ("AD_SPC1", 9, _("spécial 1 (inutilisé)")),
    ("AD_SPC2", 10, _("spécial 2 (inutilisé)")),
    ("AD_BLND", 11, _("aveugle (flash)")),
    ("AD_STUN", 12, _("étourdit")),
    ("AD_SLOW", 13, _("ralentit")),
    ("AD_PLYS", 14, _("paralyse (taser)")),
    ("AD_DRLI", 15, _("draine les niveaux")),
    ("AD_DREN", 16, _("draine l'énergie")),
    ("AD_LEGS", 17, _("blesse les jambes")),
    ("AD_STON", 18, _("pétrifie")),
    ("AD_STCK", 19, _("colle (aimant, grappin)")),
    ("AD_SGLD", 20, _("vole l'argent")),
    ("AD_SITM", 21, _("vole un objet")),
    ("AD_SEDU", 22, _("séduit et vole")),
    ("AD_TLPT", 23, _("téléporte")),
    ("AD_RUST", 24, _("rouille l'armure")),
    ("AD_CONF", 25, _("rend confus (brouillage)")),
    ("AD_DGST", 26, _("digère")),
    ("AD_HEAL", 27, _("soigne (robot médical)")),
    ("AD_WRAP", 28, _("enserre (noie)")),
    ("AD_WERE", 29, _("lycanthropie")),
    ("AD_DRDX", 30, _("draine la dextérité")),
    ("AD_DRCO", 31, _("draine la constitution")),
    ("AD_DRIN", 32, _("draine l'intelligence")),
    ("AD_DISE", 33, _("maladie")),
    ("AD_DCAY", 34, _("pourrit l'organique")),
    ("AD_SSEX", 35, _("séduction étendue")),
    ("AD_HALU", 36, _("hallucinations")),
    ("AD_DETH", 37, _("Mort (cavalier)")),
    ("AD_PEST", 38, _("Pestilence (cavalier)")),
    ("AD_FAMN", 39, _("Famine (cavalier)")),
    ("AD_SLIM", 40, _("change en slime")),
    ("AD_ENCH", 41, _("désenchante")),
    ("AD_CORR", 42, _("corrode l'armure")),
    ("AD_POLY", 43, _("polymorphe")),
    ("AD_CLRC", 240, _("sort de prêtre au hasard")),
    ("AD_SPEL", 241, _("sort de mage au hasard")),
    ("AD_RBRE", 242, _("souffle au hasard")),
    ("AD_SAMU", 252, _("frappe, vole l'Amulette")),
    ("AD_CURS", 253, _("malédiction (gremlin)")),
]
AT_VALUE = {n: v for n, v, _ in ATTACK_TYPES}
AD_VALUE = {n: v for n, v, _ in DAMAGE_TYPES}
AT_DESC = {n: d for n, _, d in ATTACK_TYPES}
AD_DESC = {n: d for n, _, d in DAMAGE_TYPES}
RANGED_AT = ("AT_SPIT", "AT_BREA", "AT_GAZE")
NO_ATTK = ["AT_NONE", "AD_PHYS", 0, 0]

# --- sons, tailles (monflag.h) -----------------------------------------
SOUNDS = [
    ("MS_SILENT", 0, _("silencieux")), ("MS_BARK", 1, _("aboie")),
    ("MS_MEW", 2, _("miaule")), ("MS_ROAR", 3, _("rugit")),
    ("MS_BELLOW", 4, _("mugit")), ("MS_GROWL", 5, _("grogne")),
    ("MS_SQEEK", 6, _("couine")), ("MS_SQAWK", 7, _("piaille")),
    ("MS_CHIRP", 8, _("pépie")), ("MS_HISS", 9, _("siffle (vapeur)")),
    ("MS_BUZZ", 10, _("bourdonne (rotors)")),
    ("MS_GRUNT", 11, _("grogne (langage)")), ("MS_NEIGH", 12, _("hennit")),
    ("MS_MOO", 13, _("meugle")), ("MS_WAIL", 14, _("gémit")),
    ("MS_GURGLE", 15, _("gargouille")), ("MS_BURBLE", 16, _("glougloute")),
    ("MS_TRUMPET", 17, _("barrit")), ("MS_SHRIEK", 18, _("hurle (alarme)")),
    ("MS_BONES", 19, _("cliquette")), ("MS_LAUGH", 20, _("rit")),
    ("MS_MUMBLE", 21, _("marmonne")), ("MS_IMITATE", 22, _("imite")),
    ("MS_WERE", 23, _("lycanthrope")), ("MS_ORC", 24, _("brute")),
    ("MS_HUMANOID", 25, _("parle (humanoïde)")),
    ("MS_ARREST", 26, _("« Halte, police ! »")),
    ("MS_SOLDIER", 27, _("soldat")), ("MS_GUARD", 28, _("garde")),
    ("MS_DJINNI", 29, _("djinn")), ("MS_NURSE", 30, _("infirmière")),
    ("MS_SEDUCE", 31, _("séduit")), ("MS_VAMPIRE", 32, _("vampire")),
    ("MS_BRIBE", 33, _("réclame de l'argent")), ("MS_CUSS", 34, _("insulte")),
    ("MS_RIDER", 35, _("cavalier")), ("MS_LEADER", 36, _("chef de quête")),
    ("MS_NEMESIS", 37, _("némésis")), ("MS_GUARDIAN", 38, _("gardien")),
    ("MS_SELL", 39, _("vend")), ("MS_ORACLE", 40, _("oracle")),
    ("MS_PRIEST", 41, _("prêtre")), ("MS_SPELL", 42, _("lanceur de sorts")),
    ("MS_BOAST", 43, _("se vante (géant)")), ("MS_GROAN", 44, _("geint")),
]
SIZES = [
    ("MZ_TINY", 0, _("minuscule (< 60 cm)")),
    ("MZ_SMALL", 1, _("petit (60 cm - 1,20 m)")),
    ("MZ_MEDIUM", 2, _("moyen (taille humaine)")),
    ("MZ_LARGE", 3, _("grand (2 - 3,60 m)")),
    ("MZ_HUGE", 4, _("énorme (3,60 - 7,50 m)")),
    ("MZ_GIGANTIC", 7, _("gigantesque")),
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
    "CLR_BLACK": _("noir (bleu foncé)"), "CLR_RED": _("rouge"),
    "CLR_GREEN": _("vert"), "CLR_BROWN": _("brun"), "CLR_BLUE": _("bleu"),
    "CLR_MAGENTA": _("magenta"), "CLR_CYAN": _("cyan"), "CLR_GRAY": _("gris"),
    "CLR_ORANGE": _("orange"), "CLR_BRIGHT_GREEN": _("vert vif"),
    "CLR_YELLOW": _("jaune"), "CLR_BRIGHT_BLUE": _("bleu vif"),
    "CLR_BRIGHT_MAGENTA": _("magenta vif (néon)"),
    "CLR_BRIGHT_CYAN": _("cyan vif (néon)"), "CLR_WHITE": _("blanc"),
    "HI_DOMESTIC": _("domestique (blanc)"), "HI_LORD": _("seigneur (magenta)"),
    "HI_OVERLORD": _("suzerain (magenta vif)"), "HI_METAL": _("métal (cyan)"),
    "HI_COPPER": _("cuivre (jaune)"), "HI_SILVER": _("argent (gris)"),
    "HI_GOLD": _("or (jaune)"), "HI_LEATHER": _("cuir (brun)"),
    "HI_CLOTH": _("tissu (brun)"), "HI_ORGANIC": _("organique (brun)"),
    "HI_WOOD": _("bois (brun)"), "HI_PAPER": _("papier (blanc)"),
    "HI_GLASS": _("verre (cyan vif)"), "HI_MINERAL": _("minéral (gris)"),
    "HI_ZAP": _("rayon (bleu vif)"), "DRAGON_SILVER": _("argent (cyan vif)"),
}

# --- poids nommés (weight.h) -------------------------------------------
WEIGHTS = {
    "WT_ETHEREAL": 0, "WT_JELLY": 50, "WT_NYMPH": 600, "WT_ELF": 800,
    "WT_HUMAN": 1450, "WT_BABY_DRAGON": 1500, "WT_DRAGON": 4500,
}

# --- résistances (MR_*), conférées en mangeant le cadavre ---------------
RESISTS = [
    ("MR_FIRE", 0x01, _("feu")), ("MR_COLD", 0x02, _("froid")),
    ("MR_SLEEP", 0x04, _("sommeil")), ("MR_DISINT", 0x08, _("désintégration")),
    ("MR_ELEC", 0x10, _("électricité")), ("MR_POISON", 0x20, _("poison")),
    ("MR_ACID", 0x40, _("acide")), ("MR_STONE", 0x80, _("pétrification")),
]

# --- génération (G_*) ---------------------------------------------------
GENFLAGS = [
    ("G_UNIQ", 0x1000, _("unique (créé une seule fois)")),
    ("G_NOHELL", 0x0800, _("jamais dans la Géhenne")),
    ("G_HELL", 0x0400, _("seulement dans la Géhenne")),
    ("G_NOGEN", 0x0200, _("jamais au hasard (niveaux spéciaux)")),
    ("G_SGROUP", 0x0080, _("en petits groupes")),
    ("G_LGROUP", 0x0040, _("en grands groupes")),
    ("G_GENO", 0x0020, _("peut être génocidé")),
    ("G_NOCORPSE", 0x0010, _("ne laisse pas de cadavre (épave)")),
]

# --- drapeaux M1, M2, M3 ------------------------------------------------
FLAGS1 = [
    ("M1_FLY", 0x00000001, _("vole ou flotte")),
    ("M1_SWIM", 0x00000002, _("traverse l'eau")),
    ("M1_AMORPHOUS", 0x00000004, _("passe sous les portes")),
    ("M1_WALLWALK", 0x00000008, _("traverse la roche")),
    ("M1_CLING", 0x00000010, _("s'accroche au plafond")),
    ("M1_TUNNEL", 0x00000020, _("creuse la roche (foreuse)")),
    ("M1_NEEDPICK", 0x00000040, _("creuse avec une pioche")),
    ("M1_CONCEAL", 0x00000080, _("se cache sous les objets")),
    ("M1_HIDE", 0x00000100, _("se camoufle (plafond)")),
    ("M1_AMPHIBIOUS", 0x00000200, _("survit sous l'eau")),
    ("M1_BREATHLESS", 0x00000400, _("ne respire pas")),
    ("M1_NOTAKE", 0x00000800, _("ne ramasse rien")),
    ("M1_NOEYES", 0x00001000, _("sans yeux (capteurs)")),
    ("M1_NOHANDS", 0x00002000, _("sans mains")),
    ("M1_NOLIMBS", 0x00006000, _("sans membres (inclut sans mains)")),
    ("M1_NOHEAD", 0x00008000, _("sans tête")),
    ("M1_MINDLESS", 0x00010000, _("sans esprit (automate)")),
    ("M1_HUMANOID", 0x00020000, _("corps humanoïde")),
    ("M1_ANIMAL", 0x00040000, _("corps animal")),
    ("M1_SLITHY", 0x00080000, _("corps serpentin")),
    ("M1_UNSOLID", 0x00100000, _("sans corps solide (hologramme)")),
    ("M1_THICK_HIDE", 0x00200000, _("blindé (peau épaisse)")),
    ("M1_OVIPAROUS", 0x00400000, _("pond des œufs")),
    ("M1_REGEN", 0x00800000, _("se régénère (nanites)")),
    ("M1_SEE_INVIS", 0x01000000, _("voit l'invisible")),
    ("M1_TPORT", 0x02000000, _("se téléporte")),
    ("M1_TPORT_CNTRL", 0x04000000, _("contrôle la téléportation")),
    ("M1_ACID", 0x08000000, _("acide à manger")),
    ("M1_POIS", 0x10000000, _("toxique à manger")),
    ("M1_CARNIVORE", 0x20000000, _("carnivore")),
    ("M1_HERBIVORE", 0x40000000, _("herbivore")),
    ("M1_OMNIVORE", 0x60000000, _("omnivore (carnivore + herbivore)")),
    ("M1_METALLIVORE", 0x80000000, _("mange le métal (recycleur)")),
]
FLAGS2 = [
    ("M2_NOPOLY", 0x00000001, _("le joueur ne peut pas s'y polymorpher")),
    ("M2_UNDEAD", 0x00000002, _("mort-vivant")),
    ("M2_WERE", 0x00000004, _("lycanthrope")),
    ("M2_HUMAN", 0x00000008, _("humain")),
    ("M2_ELF", 0x00000010, _("elfe")),
    ("M2_DWARF", 0x00000020, _("nain")),
    ("M2_GNOME", 0x00000040, _("gnome")),
    ("M2_ORC", 0x00000080, _("orque")),
    ("M2_DEMON", 0x00000100, _("démon")),
    ("M2_MERC", 0x00000200, _("garde ou soldat")),
    ("M2_LORD", 0x00000400, _("seigneur de son espèce")),
    ("M2_PRINCE", 0x00000800, _("suzerain de son espèce")),
    ("M2_MINION", 0x00001000, _("serviteur d'un dieu")),
    ("M2_GIANT", 0x00002000, _("géant")),
    ("M2_SHAPESHIFTER", 0x00004000, _("change de forme")),
    ("M2_MALE", 0x00010000, _("toujours mâle")),
    ("M2_FEMALE", 0x00020000, _("toujours femelle")),
    ("M2_NEUTER", 0x00040000, _("neutre (ni mâle ni femelle)")),
    ("M2_PNAME", 0x00080000, _("nom propre")),
    ("M2_HOSTILE", 0x00100000, _("toujours hostile")),
    ("M2_PEACEFUL", 0x00200000, _("toujours pacifique")),
    ("M2_DOMESTIC", 0x00400000, _("apprivoisable avec de la nourriture")),
    ("M2_WANDER", 0x00800000, _("erre au hasard (patrouille)")),
    ("M2_STALK", 0x01000000, _("vous suit d'un niveau à l'autre")),
    ("M2_NASTY", 0x02000000, _("particulièrement méchant")),
    ("M2_STRONG", 0x04000000, _("fort (ou grand)")),
    ("M2_ROCKTHROW", 0x08000000, _("lance des rochers")),
    ("M2_GREEDY", 0x10000000, _("aime l'or")),
    ("M2_JEWELS", 0x20000000, _("aime les gemmes")),
    ("M2_COLLECT", 0x40000000, _("ramasse armes et nourriture")),
    ("M2_MAGIC", 0x80000000, _("ramasse les objets magiques")),
]
FLAGS3 = [
    ("M3_WANTSAMUL", 0x0001, _("veut l'Amulette")),
    ("M3_WANTSBELL", 0x0002, _("veut la Cloche")),
    ("M3_WANTSBOOK", 0x0004, _("veut le Livre")),
    ("M3_WANTSCAND", 0x0008, _("veut le Candélabre")),
    ("M3_WANTSARTI", 0x0010, _("veut l'artefact de quête")),
    ("M3_WANTSALL", 0x001f, _("veut tous les objets majeurs")),
    ("M3_COVETOUS", 0x001f, _("convoite (= M3_WANTSALL)")),
    ("M3_WAITFORU", 0x0040, _("attend de vous voir (sentinelle)")),
    ("M3_CLOSE", 0x0080, _("vous laisse approcher")),
    ("M3_INFRAVISION", 0x0100, _("infravision (capteur thermique)")),
    ("M3_INFRAVISIBLE", 0x0200, _("visible en infravision (chaud)")),
    ("M3_DISPLACES", 0x0400, _("écarte les monstres de son chemin")),
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
        "fr_plural": "",               # vide : pluriel calculé par le jeu
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
        "after": "",                   # monstre du jeu qui le précède
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


# --- aperçu des attaques ------------------------------------------------

# verbes de hitmsg() (src/mhitu.c), traduits dans po/fr.po (« monverb »)
_HIT_VERB = {
    "AT_BITE": _("mord"), "AT_KICK": _("donne un coup de pied"),
    "AT_STNG": _("pique"), "AT_BUTT": _("donne un coup de corne"),
    "AT_TUCH": _("vous touche"), "AT_EXPL": _("explose"),
    "AT_BOOM": _("explose"),
}
# breathwep[] (src/mthrowu.c), contexte « breath »
_BREATH_NAME = {
    "AD_MAGM": _("des éclats"), "AD_FIRE": _("du feu"),
    "AD_COLD": _("du givre"),
    "AD_SLEE": _("du gaz soporifique"),
    "AD_DISN": _("un souffle de désintégration"), "AD_ELEC": _("des éclairs"),
    "AD_DRST": _("du gaz toxique"), "AD_ACID": _("de l'acide"),
}


def monnam(m):
    """« Le robot de sécurité », « L'androïde », comme Monnam() ;
    « The security bot » quand l'interface est en anglais."""
    name = m["name"] if LANG == "en" else m["fr_name"] or m["name"]
    if "G_UNIQ" in m.get("geno", []) or "M2_PNAME" in m.get("flags2", []):
        return name[:1].upper() + name[1:]
    if LANG == "en":
        return "The " + name
    if name[:1].lower() in "aâàeéèêiîoôuûœh":
        return "L'" + name
    return ("La " if m.get("fr_gender") == "f" else "Le ") + name


def average_damage(attack):
    """Dégâts moyens des dés NdM : N × (M + 1) / 2."""
    _at, _ad, n, d = attack
    return n * (d + 1) / 2 if n and d else 0.0


def attack_preview(m, attack):
    """(dégâts moyens, message affiché par le jeu, remarque)."""
    at, ad, n, d = attack
    who = monnam(m)
    avg = average_damage(attack)
    note = ""
    if at == "AT_BREA":
        msg = _("%s crache %s !") % (
            who, _BREATH_NAME.get(ad, _("un souffle étrange")))
    elif at == "AT_SPIT":
        msg = _("%s crache du venin !") % who
    elif at == "AT_ENGL":
        msg = _("%s vous engloutit !") % who
    elif at == "AT_MAGC":
        msg = _("%s lance un sort !") % who
        note = _("sort choisi selon le niveau")
    elif at == "AT_GAZE":
        msg = _("%s vous fixe du regard (%s)") % (who, AD_DESC.get(ad, "?"))
    elif at == "AT_TENT":
        msg = _("%s vous suce le cerveau avec ses tentacules !") % who
    elif at == "AT_NONE":
        msg = _("(riposte quand vous le frappez : %s)") % AD_DESC.get(ad, "?")
        if not n:
            note = _("dés selon le niveau : (niveau / 2 + 1)d%d") % (d or 4)
    else:
        msg = _("%s %s !") % (who, _HIT_VERB.get(at, _("frappe")))
        if at == "AT_WEAP":
            note = _("+ dégâts de l'arme tenue")
        elif at == "AT_HUGS":
            note = _("seulement si les deux attaques précédentes touchent")
        elif at == "AT_BOOM":
            note = _("à sa mort")
    return avg, msg, note


def average_per_turn(m):
    return sum(average_damage(a) for a in attacks_used(m)
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
        raise ValueError(_("%s attendu : %s") % (name, expr[:40]))
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
        raise ValueError(_("MON() à %d arguments") % len(args))
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


# --- pluriel français ----------------------------------------------------

_PLURAL_STOPS = [" de ", " d'", " des ", " du ", " à ", " en "]


def french_plural(tr):
    """Pluriel que le jeu forme pour un nom français : i18n_mon_plural()
    de src/do_name.c, octet pour octet (UTF-8). Chaque mot avant le
    premier complément (« de », « d' »… « en ») prend un « s », ou un
    « x » après « au » et « eu », sauf s'il finit par s, x ou z ou n'a
    qu'un octet ; les mots sont séparés par des espaces ou des traits
    d'union."""
    b = tr.encode("utf-8")
    end, rest = len(b), b""
    for st in _PLURAL_STOPS:
        i = b.find(st.encode("utf-8"))
        if i >= 0 and i < end:
            end, rest = i, b[i:]
    if not rest:
        rest = b[end:]
    out = b""
    p = 0
    while p < end:
        q = p
        while q < end and b[q:q + 1] not in (b" ", b"-"):
            q += 1
        out += b[p:q]
        if q - p >= 2 and b[q - 1:q] not in (b"s", b"x", b"z"):
            out += b"x" if b[q - 1:q] == b"u" and b[q - 2:q - 1] in (
                b"a", b"e") else b"s"
        if q < end:
            out += b[q:q + 1]
            q += 1
        p = q
    return (out + rest).decode("utf-8", errors="replace")


# exceptions courantes de la règle « + s »
_PLURAL_IRREGULAR = ("al", "ail")
_PLURAL_OU_X = ("bijou", "caillou", "chou", "genou", "hibou", "joujou",
                "pou")
_PLURAL_INVARIABLE = ("bleu", "pneu", "landau", "sarrau")


def plural_doubts(tr):
    """Raisons de douter du pluriel calculé d'un nom français."""
    out = []
    head = tr
    for st in _PLURAL_STOPS:
        i = head.find(st)
        if i >= 0:
            head = head[:i]
    words = re.split(r"[ -]", head)
    for k, w in enumerate(words):
        lw = w.lower()
        if len(w) >= 2 and w.isupper():
            out.append(_("« %s » est un sigle (invariable)") % w)
        elif k and w[:1].isupper():
            out.append(_("« %s » est un nom propre (pas de « s »)") % w)
        elif lw.endswith(_PLURAL_IRREGULAR) and len(lw) > 3:
            out.append(_("« %s » fait peut-être son pluriel en -aux") % w)
        elif lw in _PLURAL_OU_X:
            out.append(_("« %s » prend un x au pluriel") % w)
        elif lw in _PLURAL_INVARIABLE:
            out.append(_("« %s » prend un s au pluriel, pas un x") % w)
    return out


# --- vérification -------------------------------------------------------

# Dégâts que le code du jeu sait traiter pour chaque type d'attaque
# (relevés dans les sources de NetHack 5.0). Hors de ces listes, le jeu
# signale une erreur interne (« impossible ») ou l'attaque est sans effet.
_BREATH = ("AD_MAGM", "AD_FIRE", "AD_COLD", "AD_SLEE", "AD_DISN",
           "AD_ELEC", "AD_DRST", "AD_ACID")
ATTACK_RULES = {
    # type : (dégâts acceptés, gravité hors liste, explication)
    "AT_BREA": (_BREATH + ("AD_RBRE", "AD_SPC1", "AD_SPC2"), "erreur",
                _("un souffle n'existe qu'en projectiles magiques, feu, "
                "froid, sommeil, désintégration, électricité, poison, "
                "acide ou au hasard (breamu(), BZ_VALID_ADTYP)")),
    "AT_SPIT": (("AD_ACID", "AD_BLND", "AD_DRST"), "erreur",
                _("on ne crache que de l'acide ou du venin aveuglant "
                "(spitmm())")),
    "AT_GAZE": (("AD_STON", "AD_CONF", "AD_STUN", "AD_BLND", "AD_FIRE"),
                "erreur",
                _("un regard ne pétrifie, confond, étourdit, aveugle ou "
                "brûle (gazemu())")),
    "AT_EXPL": (("AD_COLD", "AD_FIRE", "AD_ELEC", "AD_BLND", "AD_HALU"),
                "erreur",
                _("une explosion au contact est de froid, de feu, "
                "électrique, aveuglante ou hallucinogène (explmu())")),
    "AT_BOOM": (("AD_PHYS",) + _BREATH, "erreur",
                _("une explosion à la destruction est physique ou du type "
                "d'un souffle (mon_explodes())")),
    "AT_MAGC": (("AD_SPEL", "AD_CLRC", "AD_FIRE", "AD_COLD", "AD_MAGM"),
                "erreur",
                _("un sort est de mage (AD_SPEL), de prêtre (AD_CLRC), de "
                "feu, de froid ou de projectiles magiques (castmu())")),
    "AT_ENGL": (("AD_DGST", "AD_PHYS", "AD_ACID", "AD_BLND", "AD_ELEC",
                 "AD_COLD", "AD_FIRE", "AD_DISE", "AD_DREN", "AD_WRAP"),
                "attention",
                _("l'engloutissement n'a pas d'effet avec ces dégâts "
                "(gulpmu())")),
    "AT_NONE": (("AD_FIRE", "AD_ACID", "AD_STON", "AD_RUST", "AD_CORR",
                 "AD_MAGM", "AD_ENCH", "AD_PLYS", "AD_COLD", "AD_STUN",
                 "AD_ELEC", "AD_SLIM"), "attention",
                _("la riposte passive n'a pas d'effet avec ces dégâts "
                "(passive())")),
}
# dégâts qui n'ont de sens qu'avec un type d'attaque précis
_ONLY_WITH = {
    "AD_RBRE": ("AT_BREA",), "AD_SPEL": ("AT_MAGC",),
    "AD_CLRC": ("AT_MAGC",), "AD_SPC1": (), "AD_SPC2": (),
}


def attack_allows(at, ad):
    """Vrai si le jeu sait traiter ce dégât pour ce type d'attaque."""
    if at in ATTACK_RULES:
        ok = ad in ATTACK_RULES[at][0]
    else:
        ok = True
    return ok and (ad not in _ONLY_WITH or at in _ONLY_WITH[ad])


def check_attacks(m):
    """Combinaisons d'attaques que le jeu ne gère pas : liste de
    (gravité, message)."""
    out = []
    passive_seen = False
    for i, (at, ad, dn, dd) in enumerate(m["attacks"]):
        if at == "AT_NONE" and ad == "AD_PHYS" and not dn and not dd:
            continue                    # emplacement vide
        n = i + 1
        if at in ATTACK_RULES and ad not in ATTACK_RULES[at][0]:
            grav, why = ATTACK_RULES[at][1], ATTACK_RULES[at][2]
            out.append((grav, _("Attaque %d (%s %s) : %s")
                        % (n, at[3:], ad[3:], why)))
        elif ad in _ONLY_WITH and at not in _ONLY_WITH[ad]:
            if _ONLY_WITH[ad]:
                out.append(("attention", _("Attaque %d : %s ne sert qu'avec "
                            "%s") % (n, ad, " ou ".join(_ONLY_WITH[ad]))))
            else:
                out.append(("attention", _("Attaque %d : %s n'est pas "
                            "utilisé par le jeu") % (n, ad)))
        elif at == "AT_BREA" and ad in ("AD_SPC1", "AD_SPC2"):
            out.append(("attention", _("Attaque %d : souffle %s sans nom "
                        "(« strange breath »)") % (n, ad)))
        if at == "AT_NONE":
            if passive_seen:
                out.append(("attention", _("Attaque %d : seule la première "
                            "riposte passive (AT_NONE) compte") % n))
            passive_seen = True
        if at == "AT_HUGS":
            prev = m["attacks"][i - 2:i] if i >= 2 else []
            if len(prev) < 2 or any(a[0] == "AT_NONE" for a in prev):
                out.append(("attention", _("Attaque %d : une étreinte ne "
                            "réussit que si les deux attaques précédentes "
                            "ont touché ; placez-la après deux attaques "
                            "au corps à corps") % n))
    return out


BN_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")


# Plages de monstres que le code du jeu parcourt dans l'ordre de mons[]
# (Dragon_to_scales(), polyself.c…) : rien ne doit s'y glisser.
LOCKED_RANGES = [("baby gray dragon", "baby yellow dragon"),
                 ("gray dragon", "yellow dragon")]


def first_blocks(game):
    """{S_classe: [noms]} du premier bloc de chaque classe, dans l'ordre
    de monsters.h (les rôles, némésis… des blocs suivants sont exclus :
    les nouveaux monstres ne vont que dans le premier bloc)."""
    out, closed, prev = {}, set(), None
    for g in game:
        if g["sym"] != prev:
            if prev is not None:
                closed.add(prev)
            prev = g["sym"]
        if g["sym"] not in closed:
            out.setdefault(g["sym"], []).append(g["name"])
    return out


def insert_choices(game, sym):
    """Monstres de la classe après lesquels on peut insérer."""
    names = first_blocks(game).get(sym, [])
    locked = set()
    for a, b in LOCKED_RANGES:
        if a in names and b in names:
            locked.update(names[names.index(a):names.index(b)])
    return [n for n in names if n not in locked]


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
        err(_("Identifiant PM_ invalide : majuscules, chiffres et _"))
    if not m["name"].strip():
        err(_("Nom anglais vide"))
    elif m["name"] != m["name"].strip() or re.search(r'["(),\\]', m["name"]):
        err(_("Nom anglais : pas d'espace au bord, ni guillemet, "
            "parenthèse, virgule ou barre oblique inverse"))
    if bool(m["name_m"]) != bool(m["name_f"]):
        err(_("Noms par genre : il faut le masculin ET le féminin"))
    others = list(game or []) + list(project or [])
    names = {m["name"], m["name_m"], m["name_f"]} - {""}
    for o in others:
        if o["bn"] == m["bn"]:
            err(_("Identifiant PM_%s déjà utilisé (%s)") % (m["bn"],
                                                           o["name"]))
        onames = {o["name"], o["name_m"], o["name_f"]} - {""}
        for n in names & onames:
            err(_("Nom « %s » déjà utilisé") % n)
    if m["after"] and game and m["after"] not in insert_choices(
            game, m["sym"]):
        err(_("Placer après « %s » : pas un monstre de la classe %s où "
              "l'on peut insérer") % (m["after"], CLASS_CHAR.get(m["sym"],
                                                                 "?")))
    if m["sym"] not in CLASS_CHAR:
        err(_("Classe inconnue : %s") % m["sym"])
    for key, lo, hi, label in (
            ("level", 0, 49, _("Niveau")), ("move", 0, 127, _("Vitesse")),
            ("ac", -128, 127, _("Classe d'armure")),
            ("mr", 0, 127, _("Résistance à la magie")),
            ("align", -128, 127, _("Alignement")),
            ("weight", 0, 65535, _("Poids")),
            ("nutrition", 0, 65535, _("Nutrition")),
            ("freq", 0, 7, _("Fréquence"))):
        if not lo <= m[key] <= hi:
            err(_("%s hors limites (%d..%d)") % (label, lo, hi))
    d = difficulty(m)
    if not 0 <= d <= 255:
        err(_("Difficulté hors limites (0..255)"))
    if m["difficulty"] is not None and m["difficulty"] != mstrength(m):
        warn(_("Difficulté manuelle %d, calculée %d")
             % (m["difficulty"], mstrength(m)))
    for i, (at, ad, dn, dd) in enumerate(m["attacks"]):
        if at not in AT_VALUE:
            err(_("Attaque %d : type %s inconnu") % (i + 1, at))
        if ad not in AD_VALUE:
            err(_("Attaque %d : dégât %s inconnu") % (i + 1, ad))
        if not (0 <= dn <= 255 and 0 <= dd <= 255):
            err(_("Attaque %d : dés hors limites (0..255)") % (i + 1))
        if at == "AT_WEAP" and has_flag(m, "flags1", "M1_NOHANDS"):
            warn(_("Attaque %d : arme sans mains (M1_NOHANDS)") % (i + 1))
        if ad in ("AD_DETH", "AD_PEST", "AD_FAMN"):
            warn(_("Attaque %d : dégât réservé aux Cavaliers") % (i + 1))
        if at == "AT_ENGL" and m["size"] in ("MZ_TINY", "MZ_SMALL"):
            warn(_("Attaque %d : engloutir demande une grande taille")
                 % (i + 1))
    out += check_attacks(m)
    used = attacks_used(m)
    if m["attacks"][:len(used)] != used:
        warn(_("Attaques : un emplacement vide avant une attaque "
             "(le jeu s'arrête au premier vide pour certaines actions)"))
    if not used:
        warn(_("Aucune attaque"))
    if m["sym"] == "S_GOLEM":
        if m["golem_hp"] <= 0:
            err(_("Classe golem : PV fixes obligatoires (sinon 0 PV)"))
        if m["level"] <= 0:
            err(_("Classe golem : niveau au moins 1 (PV par niveau)"))
    if m["sound"] not in [s for s, _, _ in SOUNDS]:
        err(_("Son inconnu : %s") % m["sound"])
    if m["size"] not in [s for s, _, _ in SIZES]:
        err(_("Taille inconnue : %s") % m["size"])
    if m["color"] not in COLOR_VALUE:
        err(_("Couleur inconnue : %s") % m["color"])
    for field in ("mr1", "mr2", "geno", "flags1", "flags2", "flags3"):
        for n in m[field]:
            if n not in FLAG_VALUE:
                err(_("Drapeau inconnu : %s") % n)
    f2 = m["flags2"]
    if "M2_HOSTILE" in f2 and "M2_PEACEFUL" in f2:
        err(_("À la fois hostile et pacifique"))
    sexes = [x for x in ("M2_MALE", "M2_FEMALE", "M2_NEUTER") if x in f2]
    if len(sexes) > 1:
        err(_("Plusieurs sexes : %s") % ", ".join(sexes))
    if "G_HELL" in m["geno"] and "G_NOHELL" in m["geno"]:
        err(_("G_HELL et G_NOHELL à la fois"))
    if "G_NOGEN" not in m["geno"] and "G_UNIQ" not in m["geno"] \
            and m["freq"] == 0:
        warn(_("Fréquence 0 : jamais créé au hasard (ajoutez G_NOGEN)"))
    if "G_NOCORPSE" not in m["geno"] and m["nutrition"] == 0:
        warn(_("Laisse un cadavre de valeur nutritive nulle "
             "(G_NOCORPSE pour une épave de robot)"))
    if m["fr_name"][:1].isupper() and not has_flag(m, "flags2", "M2_PNAME"):
        warn(_("Nom français avec majuscule : il restera ainsi au milieu "
             "des phrases (« le Mecha… ») ; M2_PNAME pour un nom propre"))
    if not m["fr_name"].strip():
        warn(_("Pas de nom français : le jeu affichera le nom anglais"))
    elif not m["fr_plural"].strip() and "G_UNIQ" not in m["geno"] \
            and "M2_PNAME" not in m["flags2"]:
        for why in plural_doubts(m["fr_name"]):
            warn(_("Pluriel calculé « %s » : %s ; corrigez-le dans "
                 "« Pluriel français »") % (french_plural(m["fr_name"]), why))
    if m["fr_gender"] not in ("m", "f"):
        err(_("Genre français : m ou f"))
    if m["name_m"] and not (m["fr_name_m"] and m["fr_name_f"]):
        warn(_("Noms par genre sans leur traduction française"))
    if m["tile_shape"] == "personnalisée" and \
            not any(c != "." for row in m["tile"] for c in row):
        warn(_("Tuile personnalisée vide (interfaces graphiques seulement)"))
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
            key, _sep, rest = s.partition(" ")
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
