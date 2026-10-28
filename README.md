# nhmonedit — éditeur de monstres NetHack, version Night City

Éditeur plein écran en mode terminal (Python 3 + curses, sans dépendance
externe) pour créer les **robots et mechas** de NetHack 5.0 cyberpunk
(branche `cybernethack`) et les ajouter au jeu.

Il complète l'éditeur de cartes `../NetHack_MapEditor`.

## Lancement

```sh
./nhmonedit.sh                      # projet monstres.json, sources ../NetHack-5.0.0
./nhmonedit.sh mes-robots.json      # autre projet
./nhmonedit.sh --src ~/NetHack-5.0.0
./nhmonedit.sh --install            # lien ~/.local/bin/nhmonedit
```

Variables : `NHMONEDIT_SRC` (sources du jeu), `NHMONEDIT_HACKDIR`
(dossier du jeu installé, par défaut `~/nh/install/games/lib/nethackdir`).

Terminal de 80×24 au minimum ; à partir de 120 colonnes, un panneau
« Aperçu » montre la difficulté, les PV, la tuile et les problèmes du
monstre en direct.

## Ce que l'on peut régler

Tout ce que contient une entrée `MON()` de `include/monsters.h` :

- **identité** : nom français (affiché dans le jeu, thème `fr@cyber`) et
  son genre, nom anglais (nom interne, à taper avec Ctrl-G en mode
  wizard), identifiant `PM_`, noms par genre facultatifs ;
- **apparence** : classe (lettre sur la carte), couleur, tuile 16×16 pour
  les interfaces graphiques (éditeur de pixels intégré) ;
- **caractéristiques** : niveau, vitesse, classe d'armure, résistance à
  la magie, alignement, PV fixes pour la classe golem ;
- **génération** : fréquence, unique, groupes, génocide, cadavre ;
- **six attaques** : type (arme, souffle, regard, explosion…), dégâts
  (feu, électricité, paralysie, rouille…) et dés ;
- **corps** : poids, nutrition, son, taille, résistances, résistances
  conférées, drapeaux M1/M2/M3 ;
- **encyclopédie** en français et en anglais (commandes `;` et `/`).

La **difficulté** est calculée comme dans le jeu (`mstrength()` de
`src/mondata.c` ; le calcul retrouve celle de 380 des 382 monstres du
jeu) ; on peut la forcer. La touche `b` compare le monstre aux monstres
du jeu de difficulté proche, pour l'équilibrage.

## Modèles

`n` propose des modèles prêts à adapter, avec leur tuile et leur texte
d'encyclopédie : robot de sécurité, drone de surveillance, drone
d'assaut, drone kamikaze, araignée-robot, androïde, robot recycleur,
mecha de combat, mecha titan, tourelle de sécurité, robot vierge.

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
| `t` | dessiner la tuile |
| `v` `c` `b` | vérifier, voir le code C, comparer |
| `I` `R` | intégrer aux sources, retirer des sources |
| `m` `U` `j` | compiler, mettre à jour le jeu installé, jouer |
| `s` `u` `?` `q` | enregistrer, annuler, aide, quitter |

Éditeur de tuile : flèches pour se déplacer, Espace pour peindre, une
lettre de la palette (`A`–`Z`, `.`, `0`, `1`) pour choisir la couleur
et peindre, `f` remplir, `p` pipette, `r` remplacer une couleur, `m`
symétrie, `h` retourner, `g` silhouette (humanoïde, mecha, drone,
sphère, araignée, chenilles), `u` annuler, Échap pour terminer.

## Du projet au jeu

1. **`I` — intégrer.** L'éditeur vérifie les monstres, montre les
   différences, puis écrit dans les sources (après une copie des fichiers
   dans `sauvegardes/<date>/`) :

   | Fichier | Ajout |
   |---|---|
   | `include/monsters.h` | l'entrée `MON()`, à la fin de la classe choisie |
   | `src/makemon.c` | les PV fixes dans `golemhp()` (classe golem) |
   | `win/share/monsters.txt` | les tuiles mâle et femelle |
   | `po/fr.po`, `po/themes/fr@cyber.po`, `po/nethack.pot` | nom français et genre |
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

4. **`j` — jouer** en mode wizard : Ctrl-G puis le nom **anglais** du
   monstre pour le faire apparaître, `;` pour le regarder.

**Attention :** ajouter un monstre change la liste `mons[]` : les
parties sauvegardées et les fichiers de bones d'avant ne se chargent
plus (c'est le rôle de `EDITLEVEL`).

## Vérifications

L'éditeur signale (panneau « Aperçu », touche `v`) : identifiant ou nom
déjà pris par le jeu, valeurs hors limites des champs C, golem sans PV
fixes, arme sans mains, hostile et pacifique à la fois, plusieurs sexes,
fréquence nulle sans `G_NOGEN`, nom français manquant ou avec majuscule,
tuile vide… L'intégration est refusée tant qu'il reste une erreur.

## Fichiers

| Fichier | Rôle |
|---|---|
| `nhmonedit.py` | l'application (fiche, liste, actions) |
| `nhmon_ui.py` | fenêtres curses, menus, éditeur de texte et de tuile |
| `nhmon_data.py` | constantes du jeu, lecture de `monsters.h`, difficulté, code C, vérifications |
| `nhmon_install.py` | intégration et retrait dans les sources |
| `nhmon_templates.py` | modèles de robots et silhouettes de tuiles |
| `tests/test_nhmon.py` | tests (`python3 -m unittest discover -s tests`) |
| `monstres.json` | le projet par défaut (créé au premier enregistrement) |

## Environnement de test

Développé sous Lubuntu 26.04 avec Python 3.14 et NetHack 5.0.0, branche
`cybernethack`. Testé : compilation complète avec dix robots intégrés
(aucun avertissement), `tilemap` sans erreur, apparition en jeu
(« Un mecha de combat apparaît à côté de vous. »), retrait qui rend les
fichiers à l'identique.
