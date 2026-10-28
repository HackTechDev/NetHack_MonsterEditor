# nhmonedit — éditeur de monstres NetHack, version Night City

Éditeur plein écran en mode terminal (Python 3 + curses, sans dépendance
externe) pour créer les **robots et mechas** de NetHack 5.0 cyberpunk
(branche `cybernethack`) et les ajouter au jeu.

Il complète l'éditeur de cartes `../NetHack_MapEditor`.

**Premiers pas :** le [tutoriel](TUTORIAL.md) crée un robot de A à Z ;
la liste complète des fonctions est dans [FEATURES.md](FEATURES.md).

## Lancement

```sh
./nhmonedit.sh                      # projet monstres.json, sources ../NetHack-5.0.0
./nhmonedit.sh mes-robots.json      # autre projet
./nhmonedit.sh --src ~/NetHack-5.0.0
./nhmonedit.sh --install            # lien ~/.local/bin/nhmonedit
```

Variables : `NHMONEDIT_SRC` (sources du jeu), `NHMONEDIT_HACKDIR`
(dossier du jeu installé, par défaut `~/nh/install/games/lib/nethackdir`),
`NHMONEDIT_MOUSE=0` (sans souris), `NHMONEDIT_LANG=en` ou `fr` (langue de
l'interface ; par défaut celle de la locale).

Ces réglages peuvent aussi aller dans `~/.config/nhmonedit/config`
(sources, jeu installé, options de `make` comme `WANT_WIN_ALL=1`,
projet par défaut, langue, souris, sauvegarde de secours) : voir
[`config.exemple`](config.exemple).

Terminal de 80×24 au minimum ; à partir de 120 colonnes, un panneau
« Aperçu » montre la difficulté, les PV et les problèmes du monstre en
direct.

## Ce que l'on peut régler

Tout ce que contient une entrée `MON()` de `include/monsters.h` :

- **identité** : nom français (affiché dans le jeu, thème `fr@cyber`),
  son genre et son pluriel (calculé comme le jeu, à corriger quand il se
  trompe : « sentinelles Arasakas »), nom anglais (nom interne, à taper avec Ctrl-G en mode
  wizard), identifiant `PM_`, noms par genre facultatifs ;
- **apparence** : classe (lettre sur la carte) et couleur ;
- **caractéristiques** : niveau, vitesse, classe d'armure, résistance à
  la magie, alignement, PV fixes pour la classe golem ;
- **génération** : fréquence, unique, groupes, génocide, cadavre ;
- **six attaques** : type (arme, souffle, regard, explosion…), dégâts
  (feu, électricité, paralysie, rouille…) et dés ;
- **corps** : poids, nutrition, son, taille, résistances, résistances
  conférées, drapeaux M1/M2/M3 ;
- **encyclopédie** en français et en anglais (commandes `;` et `/`).

### La tuile

Dans le terminal, un monstre n'est qu'une lettre colorée : la tuile
16×16 ne se voit que dans les versions graphiques (Qt, X11). Le jeu en
exige pourtant une par monstre dans `win/share/monsters.txt` (sinon les
images de tous les monstres suivants seraient décalées). L'éditeur la
fabrique donc tout seul à partir d'une **silhouette** (humanoïde,
mecha, drone, sphère, araignée, chenilles), colorée d'après la couleur
du monstre. Par défaut (« auto »), la silhouette dépend de la classe.

Pour qui joue en graphique, `t` ouvre un éditeur de pixels ; la tuile
dessinée (ou importée du jeu avec `i`) est alors « personnalisée ».

La **difficulté** est calculée comme dans le jeu (`mstrength()` de
`src/mondata.c` ; le calcul retrouve celle de 380 des 382 monstres du
jeu) ; on peut la forcer. La touche `b` compare le monstre aux monstres
du jeu de difficulté proche, pour l'équilibrage.

## Modèles

`n` propose des modèles prêts à adapter, avec leur silhouette et leur
texte d'encyclopédie : robot de sécurité, drone de surveillance, drone
d'assaut, drone kamikaze, araignée-robot, androïde, robot recycleur,
mecha de combat, mecha titan, tourelle de sécurité, robot vierge.

Vos propres modèles s'ajoutent à la liste : menu Projet (`p`),
« Enregistrer le monstre comme modèle… » (fichier
`~/.config/nhmonedit/modeles.json`, commun à tous les projets).

`i` importe n'importe quel monstre du jeu (avec son nom français, sa
tuile et ses PV de golem) comme point de départ ; il est renommé « mk II ».

Conseil de classe pour un robot : la classe golem (`'`) donne des PV
fixes et les propriétés des créatures artificielles ; `H` convient aux
grands mechas, `e` aux sphères et drones-caméras, `B` aux drones volants,
`s` aux araignées mécaniques, `@` aux androïdes.

## Touches

| Touche | Action |
|---|---|
| Tab | passer de la liste à la fiche |
| ↑ ↓ | monstre / champ précédent ou suivant |
| ← → | changer la valeur (nombre, choix, nombre de dés) |
| Entrée | modifier le champ |
| Suppr | vider le champ (attaque, texte) ; dans la liste : supprimer |
| `n` `d` `i` | nouveau, dupliquer, importer du jeu |
| `<` `>` | déplacer le monstre dans la liste |
| `/` | aller à un monstre (tapez une partie de son nom) |
| `t` | dessiner la tuile à la main (versions graphiques seulement) |
| `v` `c` `b` `B` | vérifier, voir le code C, comparer, fiche comparée |
| `I` `R` | intégrer aux sources, retirer des sources |
| `m` `U` `j` | compiler, mettre à jour le jeu installé, jouer |
| `p` | menu du projet : fusionner un autre projet, exporter ou importer un monstre, modèles personnels |
| `s` `u` Ctrl-R `?` `q` | enregistrer, annuler, rétablir, aide, quitter |

**Souris** : un clic choisit un monstre ou un champ, un double clic
ouvre la fiche ou modifie le champ, la molette fait défiler ; dans les
menus, un second clic valide. Pour sélectionner du texte dans le
terminal, maintenir Maj ; `NHMONEDIT_MOUSE=0` coupe la souris.

Éditeur de tuile (facultatif) : flèches pour se déplacer, Espace pour peindre, une
lettre de la palette (`A`–`Z`, `.`, `0`, `1`) pour choisir la couleur
et peindre, `f` remplir, `p` pipette, `r` remplacer une couleur, `m`
symétrie, `h` retourner, `g` silhouette (humanoïde, mecha, drone,
sphère, araignée, chenilles), `u` annuler, Échap pour terminer. À la
souris : clic ou glissé pour peindre, clic droit pipette, molette ou
clic sur la palette pour la couleur.

## Du projet au jeu

1. **`I` — intégrer.** L'éditeur vérifie les monstres, montre les
   différences, puis écrit dans les sources (après une copie des fichiers
   dans `sauvegardes/<date>/`) :

   | Fichier | Ajout |
   |---|---|
   | `include/monsters.h` | l'entrée `MON()`, à la fin de la classe choisie |
   | `src/makemon.c` | les PV fixes dans `golemhp()` (classe golem) |
   | `win/share/monsters.txt` | les tuiles mâle et femelle |
   | `po/fr.po`, `po/themes/fr@cyber.po`, `po/nethack.pot` | nom français, genre et pluriel corrigé |
   | `dat/data.base`, `dat/data-fr.base`, `dat/data-fr@cyber.base` | encyclopédie |
   | `include/patchlevel.h` | `EDITLEVEL` + 1 quand la liste des monstres change |

   Chaque ajout est marqué `nhmonedit` : une nouvelle intégration
   remplace la précédente par le contenu **du projet ouvert**, et `R`
   rend les fichiers dans leur état d'origine (seul `EDITLEVEL` reste
   augmenté). `git diff` dans les sources montre aussi tout ce qui a
   changé.

2. **`m` — compiler** (`make -j`) dans les sources.

3. **`U` — mettre à jour le jeu installé** (`make update`) : contrairement
   à `make install`, `sysconf`, les scores et les sauvegardes sont
   conservés.

4. **`j` — jouer** en mode wizard. Avec tmux, le jeu s'ouvre à côté de
   l'éditeur et le monstre choisi y est créé tout seul ; `j` en crée
   d'autres tant que la partie tourne. Sinon : Ctrl-G puis le nom **anglais** du
   monstre pour le faire apparaître, `;` pour le regarder.

**Attention :** ajouter un monstre change la liste `mons[]` : les
parties sauvegardées et les fichiers de bones d'avant ne se chargent
plus (c'est le rôle de `EDITLEVEL`).

## Vérifications

L'éditeur signale (panneau « Aperçu », touche `v`) : combinaisons
d'attaques que le jeu ne gère pas (souffle paralysant, regard
endormant…), identifiant ou nom déjà pris par le jeu, valeurs hors limites des champs C, golem sans PV
fixes, arme sans mains, hostile et pacifique à la fois, plusieurs sexes,
fréquence nulle sans `G_NOGEN`, nom français manquant ou avec majuscule,
tuile personnalisée vide… L'intégration est refusée tant qu'il reste une erreur.

Tant que le projet n'est pas enregistré, une **sauvegarde de secours**
(`projet.json.nhmonedit-autosave`) est écrite chaque minute et proposée
au lancement suivant si l'éditeur a été interrompu.

## Fichiers

| Fichier | Rôle |
|---|---|
| `nhmonedit.py` | l'application (fiche, liste, actions) |
| `nhmon_ui.py` | fenêtres curses, menus, éditeur de texte et de tuile |
| `nhmon_data.py` | constantes du jeu, lecture de `monsters.h`, difficulté, code C, vérifications |
| `nhmon_install.py` | intégration et retrait dans les sources |
| `nhmon_project.py` | fichiers : projets, fusion, monstres exportés, modèles personnels |
| `nhmon_config.py` | fichier de configuration (`config.exemple`) |
| `nhmon_game.py` | essai en jeu (tmux, Ctrl-G) |
| `nhmon_templates.py` | modèles de robots, silhouettes et fabrication des tuiles |
| `nhmon_i18n.py`, `nhmon_i18n_en.py` | choix de la langue, traduction anglaise de l'interface |
| `tests/` | tests (`python3 -m unittest discover -s tests`) |
| `monstres.json` | le projet par défaut (créé au premier enregistrement) |

## Environnement de test

Développé sous Lubuntu 26.04 avec Python 3.14 et NetHack 5.0.0, branche
`cybernethack`. Testé : compilation complète avec dix robots intégrés
(aucun avertissement), `tilemap` sans erreur, apparition en jeu
(« Un mecha de combat apparaît à côté de vous. »), retrait qui rend les
fichiers à l'identique.
