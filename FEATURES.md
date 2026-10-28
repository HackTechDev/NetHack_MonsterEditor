# Fonctionnalités de nhmonedit

Liste complète de ce que fait l'éditeur. Pour apprendre à s'en servir,
voir le [tutoriel](TUTORIAL.md) ; pour les touches et les fichiers
touchés, le [README](README.md) ou `?` dans l'éditeur.

## Généralités

- Éditeur plein écran en mode terminal, écrit en Python 3 avec `curses`,
  sans aucune dépendance externe.
- Crée des monstres pour NetHack 5.0 (branche `cybernethack`) et les
  ajoute aux sources du jeu ; pensé pour les robots et les mechas de
  Night City, mais tout monstre est possible.
- Interface en français, saisie des accents (UTF-8).
- Utilisable entièrement au clavier.
- Annulation (`u`) des 100 dernières modifications du projet.
- Lanceur `nhmonedit.sh`, utilisable depuis un lien symbolique ;
  `--install` crée la commande `nhmonedit` dans `~/.local/bin`.
- Sources du jeu choisies par `--src` ou `NHMONEDIT_SRC` (par défaut
  `../NetHack-5.0.0`) ; jeu installé cherché dans `NHMONEDIT_HACKDIR`,
  `~/nh/install/games/lib/nethackdir` ou `playground` des sources.

## Affichage

- Trois zones : la liste des monstres du projet, la fiche du monstre
  choisi, et, à partir de 120 colonnes, le panneau **Aperçu** ;
  terminal de 80×24 au minimum.
- Liste : symbole du monstre dans sa couleur du jeu, nom français, et
  une pastille d'état : ● intégré aux sources, ◐ intégré mais modifié
  depuis, ✖ erreur à corriger.
- Fiche en sections (identité, caractéristiques, génération, attaques,
  corps, apparence et textes) ; chaque valeur est expliquée en clair
  (« TUCH PLYS 1d4 contact / paralyse », « -5 (chaotique) », « 10
  (calculée) »…).
- Ligne d'aide du champ sélectionné en bas de l'écran (unités,
  valeurs de référence du jeu : « humain : 1450 », « golem de fer :
  120 »…).
- Panneau Aperçu, mis à jour à chaque touche : difficulté, points de
  vie (fixes pour un golem, sinon dés et moyenne), dégâts maximaux par
  tour, vitesse en clair, état dans les sources, problèmes détectés.
- Couleurs néon (magenta et cyan) ; les couleurs des monstres suivent
  celles du jeu en mode terminal (CLR_BLACK en bleu, couleurs vives en
  gras).

## Création de monstres

- **Modèles** (`n`), avec caractéristiques, silhouette et texte
  d'encyclopédie (en français et en anglais) :
  robot de sécurité, drone de surveillance, drone d'assaut, drone
  kamikaze, araignée-robot, androïde, robot recycleur, mecha de combat,
  mecha titan, tourelle de sécurité, robot vierge.
- Noms français et anglais demandés à la création ; l'identifiant C
  (`PM_…`) est déduit du nom anglais (accents et ponctuation retirés).
- **Import** (`i`) de n'importe lequel des 382 monstres du jeu comme
  base : nom français du thème cyber, genre, PV de golem lus dans
  `golemhp()`, tuile du jeu ; la liste se filtre en tapant.
- **Duplication** (`d`) pour faire des variantes.
- Noms uniques garantis : un nom ou identifiant déjà pris (par le jeu
  ou le projet) reçoit un suffixe « mk II », « mk III »…
- Suppression (`Suppr` ou `X` dans la liste) avec confirmation,
  réordonnancement (`<`, `>`).

## Champs d'un monstre

Tous les champs d'une entrée `MON()` de `include/monsters.h`.

- **Identité** : nom français et son genre grammatical, nom anglais
  (nom interne), identifiant C, noms anglais et français par genre
  (facultatifs, comme « dwarf lord » / « dwarf lady »).
- **Classe** : les 57 classes du jeu, avec leur lettre et un conseil
  pour les robots (golem `'` pour des PV fixes, `H` pour les mechas,
  `e` et `B` pour les drones…).
- **Couleur** : 31 couleurs et alias du jeu (`CLR_*`, `HI_METAL`,
  `HI_LORD`…), affichées dans leur teinte.
- **Caractéristiques** : niveau, vitesse, classe d'armure, résistance à
  la magie, alignement (dont « sans alignement », `A_NONE`), PV fixes
  des golems.
- **Difficulté** : calculée automatiquement ou forcée (voir plus bas).
- **Génération** : fréquence (0 à 7) et 8 drapeaux `G_` (unique,
  groupes, Géhenne, génocide, cadavre…).
- **Six attaques** : 17 types (arme, griffe, souffle, regard, explosion,
  sort…) et 49 sortes de dégâts (feu, électricité, paralysie, rouille,
  vol…), chacune décrite en français et adaptée aux robots
  (« souffle (lance-flammes) », « regard (laser optique) ») ; dés au
  format `NdM`.
- **Corps** : poids, nutrition, 45 sons, 6 tailles.
- **Résistances** et résistances conférées par le cadavre (8 chacune).
- **Drapeaux** : 33 `M1` (corps et déplacement), 31 `M2` (nature et
  comportement), 12 `M3` (infravision, attente, convoitise…), chacun
  décrit en français.
- **Encyclopédie** en français et en anglais, **notes** personnelles
  (non intégrées au jeu).
- **Silhouette** de la tuile (voir « Tuiles »).

## Saisie

- `↑ ↓` changent de champ, `← →` (ou `+ -`) modifient directement :
  nombre avec un pas adapté (5 pour la résistance à la magie, 50 pour
  le poids…), choix suivant ou précédent, nombre de dés d'une attaque,
  difficulté forcée.
- `Entrée` ouvre la saisie complète : ligne de texte (avec `Ctrl-U`,
  début, fin, suppression), nombre borné avec message si la valeur est
  invalide, menu filtrable, cases à cocher.
- Menus filtrables : quelques lettres tapées réduisent la liste (sur le
  nom C et sur la description française).
- Attaque en trois temps : type, dégâts, dés.
- `Suppr` vide un champ : texte, difficulté forcée (retour au calcul),
  attaque (les suivantes remontent).
- Éditeur de texte multiligne pour l'encyclopédie, avec retour à la
  ligne à l'affichage.
- Changer le nom anglais met à jour l'identifiant C tant qu'il n'a pas
  été choisi à la main.

## Difficulté et équilibrage

- Difficulté calculée comme dans le jeu (`mstrength()` de
  `src/mondata.c`, recopiée en Python) : le calcul retrouve celle de
  380 des 382 monstres du jeu (les deux autres sont des valeurs
  ajustées à la main dans le jeu).
- Difficulté forçable, avec un avertissement si elle s'écarte du
  calcul.
- Comparaison (`b`) avec les 30 monstres du jeu de difficulté la plus
  proche : nom français, niveau, vitesse, CA, difficulté, dégâts
  maximaux, dans leur couleur.

## Vérification

En direct dans l'Aperçu et la liste, et pour tout le projet avec `v`.
Les erreurs (✖) bloquent l'intégration ; les avertissements (⚠) non.

- Erreurs : identifiant C invalide ou déjà pris, nom anglais vide, déjà
  pris ou contenant un caractère qui casserait les fichiers du jeu
  (guillemet, parenthèse, virgule, barre oblique inverse), noms par
  genre incomplets, classe, son, taille, couleur ou drapeau inconnus,
  valeurs hors des limites des champs C (niveau 0 à 49, CA, poids…),
  dés hors limites, golem sans PV fixes ou de niveau 0, à la fois
  hostile et pacifique, plusieurs sexes, `G_HELL` avec `G_NOHELL`,
  genre français autre que m ou f.
- Avertissements : arme sans mains, dégâts réservés aux Cavaliers,
  engloutissement par un petit monstre, emplacement d'attaque vide avant
  une attaque, aucune attaque, fréquence nulle sans `G_NOGEN`, cadavre
  sans valeur nutritive, nom français absent ou avec majuscule, noms par
  genre sans traduction, difficulté forcée différente du calcul, tuile
  personnalisée vide.

## Code

- `c` montre ce qui sera écrit dans les sources : l'entrée `MON()` au
  format de `monsters.h` (lignes de 78 colonnes au plus, longues listes
  de drapeaux coupées comme dans le jeu), le cas de `golemhp()`, les
  entrées du catalogue de traduction et l'entrée d'encyclopédie.
- Le code produit est vérifié sur les 382 monstres du jeu : relu, il
  redonne exactement les mêmes valeurs.

## Tuiles

- La tuile 16×16 ne sert qu'aux versions graphiques du jeu (Qt, X11),
  mais le jeu en exige une par monstre : l'éditeur la fabrique à partir
  d'une **silhouette** (humanoïde, mecha, drone, sphère, araignée,
  chenilles), colorée d'après la couleur du monstre.
- Silhouette « auto » par défaut : choisie selon la classe (mecha pour
  `H`, sphère pour `e`, drone pour `B`, araignée pour `s`, chenilles
  pour `R`…).
- Éditeur de pixels facultatif (`t`, après un avertissement) : palette
  des 29 couleurs de `monsters.txt`, aperçu en taille réelle, pipette,
  remplissage, remplacement d'une couleur, symétrie, retournement,
  silhouettes, annulation. Une tuile dessinée ou importée du jeu devient
  « personnalisée ».
- Couleurs exactes sur les terminaux à 256 couleurs, approchées sinon.

## Intégration aux sources (`I`, `R`)

- Écrit le projet dans les sources du jeu, après vérification :
  - `include/monsters.h` : l'entrée à la fin du premier bloc de sa
    classe (les classes restent contiguës, les monstres spéciaux de fin
    de liste ne sont pas concernés) ;
  - `src/makemon.c` : les PV fixes dans `golemhp()` ;
  - `win/share/monsters.txt` : tuiles mâle et femelle à la bonne place
    (y compris après les tuiles gardées pour des monstres désactivés,
    comme « beholder »), tuiles renumérotées ;
  - `po/fr.po`, `po/themes/fr@cyber.po`, `po/nethack.pot` : nom
    français et genre (masculin explicite dans le thème) ;
  - `dat/data.base`, `dat/data-fr.base`, `dat/data-fr@cyber.base` :
    encyclopédie, placée avant les entrées à jokers (« *golem ») ;
  - `include/patchlevel.h` : `EDITLEVEL` + 1 quand la liste des monstres
    change.
- Aperçu des différences, en couleur, avant d'écrire ; confirmation avec
  la liste des fichiers.
- Copie des fichiers d'avant dans `sauvegardes/<date>/`.
- Ajouts marqués `nhmonedit` : une nouvelle intégration remplace la
  précédente (sans rien écrire si tout est déjà à jour), `R` rend les
  fichiers identiques à l'origine (seul `EDITLEVEL` reste augmenté).
- Écriture atomique (fichier temporaire puis renommage).
- Projet enregistré automatiquement après l'intégration.

## Compiler et jouer

- `m` : `make -j` dans les sources ; la compilation se déroule dans le
  terminal, avec le code de sortie et la durée.
- `U` : `make update` (et non `make install`) : `sysconf`, scores et
  sauvegardes sont conservés, le jeu précédent est gardé en
  `nethack.old`.
- `j` : lance le jeu installé en mode wizard, après un rappel (Ctrl-G
  puis le nom anglais) et un avertissement si le jeu est plus ancien
  que `monsters.h`.

## Fichiers

- Projet au format JSON (`monstres.json` par défaut, ou le fichier donné
  en argument), lisible et adapté à git ; enregistrement atomique.
- Les projets d'une version précédente s'ouvrent sans perte (champs
  manquants complétés, tuile dessinée conservée).
- Demande d'enregistrer en quittant si le projet a changé.

## Qualité

- 14 tests (`python3 -m unittest discover -s tests`) : lecture de
  `monsters.h`, constantes connues, difficulté, aller-retour du code C,
  noms français, modèles, tuiles, intégration et retrait sur une copie
  des sources, ordre des tuiles, `golemhp()`, catalogues de traduction.
- Vérifié sur une copie complète des sources : compilation sans
  avertissement avec dix robots, `tilemap` sans erreur, monstre créé en
  jeu sous son nom français.
