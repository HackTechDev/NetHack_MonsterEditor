# Améliorations possibles

Idées d'évolution pour nhmonedit, classées par thème. Chaque thème
commence par les améliorations les plus utiles, et chaque idée est
marquée selon l'effort qu'elle demande :
**[facile]** quelques heures, **[moyen]** une journée environ,
**[gros]** plusieurs jours.

Les idées réalisées seront marquées « ✅ **Fait** » ; la liste complète
de ce que fait l'éditeur aujourd'hui est dans [FEATURES.md](FEATURES.md).

## État d'avancement (2026-10-28)

| Thème | Fait | Reste |
|---|---|---|
| 1. Limites connues | 1 / 5 | tuiles graphiques, encyclopédie, projets, EDITLEVEL |
| 2. Vérification | 1 / 5 | sons, corps, équilibrage, contrôle complet |
| 3. Saisie et affichage | 6 / 6 | — |
| 4. Projets et fichiers | 5 / 5 | — |
| 5. Intégration avec le jeu | 2 / 6 | fixes, commit, annulation, sons |
| 6. Robots : nouvelles règles de jeu | 0 / 6 | tout |
| 7. Relation avec l'éditeur de cartes | 0 / 3 | tout |
| 8. Qualité du projet | 0 / 4 | tout |

Prochaines étapes conseillées : les **sons réservés** (2.2), qui comme
les attaques ne se voient qu'en jouant, et le **lien avec l'éditeur de
cartes** (7.1), qui permettra de placer les robots dans les niveaux.

## 1. Limites connues

Ce que l'éditeur fait mal ou ne vérifie pas aujourd'hui.

1. **Tuiles des versions graphiques non régénérées** **[facile]**.
   `m` lance un simple `make`, qui ne refait pas toujours `x11tiles` et
   `nhtiles.bmp` : les nouvelles tuiles n'apparaissent alors pas en Qt
   ou X11. Détecter les interfaces du jeu installé (présence de
   `x11tiles`) et compiler avec `WANT_WIN_ALL=1` dans ce cas, ou le
   proposer dans un réglage.
2. **Encyclopédie non vérifiée en jeu** **[facile]**. L'entrée est bien
   compilée dans `data.fr@cyber`, mais son affichage par `;` n'a pas été
   essayé en partie. Un test qui lit le fichier compilé avec la même
   recherche que `pager.c` (premier motif qui correspond, jokers `*` et
   `?`, exclusions `~`) le garantirait.
3. ✅ **Fait** — **Pluriel français** **[facile]**. Le jeu forme le
   pluriel lui-même
   (`i18n_mon_plural()` : « mecha de combat » → « mechas de combat »),
   mais se trompe sur certains noms (« Exo-Mecha Kenshin », mots en
   -al…). Montrer le pluriel calculé dans la fiche et ajouter un champ
   « pluriel » qui écrit l'exception (contexte `monster-plural`).
   *Réalisé : `french_plural()` reproduit `i18n_mon_plural()` octet pour
   octet, `plural_doubts()` signale noms propres, sigles et mots en -al,
   -ail, -ou ; champ « Pluriel français », exception écrite dans
   `po/themes/fr@cyber.po`. Le contrôle retrouve les exceptions déjà
   écrites dans le thème (« motos-chevaux », « IA corrompues ») et
   signale « pirate neuronal » (pluriel du jeu : « pirates
   neuronals »).*
4. **Un seul projet par jeu** **[moyen]**. Une intégration remplace tous
   les monstres ajoutés par une intégration précédente, même venus d'un
   autre projet. Retenir le projet d'origine de chaque monstre intégré
   et prévenir avant de retirer ceux d'un autre projet, ou permettre
   d'intégrer plusieurs projets à la fois.
5. **EDITLEVEL ne redescend jamais** **[facile]**. Chaque changement de
   la liste des monstres l'augmente, même un retrait qui revient à la
   liste d'origine. Mémoriser la valeur d'origine pour la rétablir quand
   les sources redeviennent identiques au jeu de départ.

## 2. Vérification

1. ✅ **Fait** — **Combinaisons d'attaques que le jeu ne gère pas**
   **[moyen]**. Le
   code du jeu n'accepte qu'une partie des dégâts pour chaque type
   d'attaque : un souffle doit avoir des dégâts entre `AD_MAGM` et
   `AD_SPC2` (`BZ_VALID_ADTYP`, `include/hack.h`), un regard n'a d'effet
   que pour les dégâts traités par `gazemu()` (pétrification,
   confusion, étourdissement, aveuglement, feu, sommeil, lenteur…), un
   sort (`AT_MAGC`) a ses propres règles (`mcastu.c`). Signaler en
   erreur les combinaisons sans effet, par exemple un souffle
   paralysant. *Réalisé : `ATTACK_RULES` et `check_attacks()` dans
   `nhmon_data.py` (erreurs et avertissements, étreinte mal placée,
   seconde riposte passive), dégâts marqués ✖ dans le menu ; aucun
   monstre du jeu n'est signalé.*
2. **Sons réservés** **[facile]**. Certains sons supposent un rôle
   précis dans le jeu (`MS_LEADER`, `MS_NEMESIS`, `MS_GUARDIAN`,
   `MS_PRIEST`, `MS_SELL`, `MS_ORACLE`, `MS_NURSE`, `MS_GUARD`…) :
   avertir quand un robot ordinaire les utilise.
3. **Cohérence du corps** **[facile]**. Avertir pour un monstre
   `M1_NOEYES` avec une attaque de regard, `M1_NOLIMBS` avec un coup de
   pied, `M1_FLY` de taille gigantesque, une vitesse 0 sans attaque à
   distance, `M2_COLLECT` avec `M1_NOTAKE`.
4. **Équilibrage** **[moyen]**. Signaler un monstre nettement plus
   dangereux que les monstres du jeu de même difficulté (dégâts par
   tour, PV, CA), et donner la profondeur à partir de laquelle il peut
   apparaître au hasard.
5. **Contrôle complet avant intégration** **[moyen]**. Compiler
   `monst.c` seul et lancer `tilemap` sur une copie temporaire des
   fichiers avant d'écrire dans les sources, pour détecter une erreur
   sans attendre la compilation complète.

## 3. Saisie et affichage

1. ✅ **Fait** — **Rétablir** **[facile]** : `u` annule, mais rien ne
   rétablit ; ajouter Ctrl-R comme dans l'éditeur de cartes.
   *Réalisé : Ctrl-R (ou Ctrl-Y) rétablit, 100 niveaux ; une nouvelle
   modification vide la pile des rétablissements.*
2. ✅ **Fait** — **Souris** **[moyen]** : choisir un monstre ou un champ
   d'un clic, faire défiler les listes à la molette, peindre la tuile à
   la souris. *Réalisé : clic et double clic dans la liste et la fiche,
   molette partout (liste, fiche, menus, cases à cocher, visionneuse),
   second clic qui valide un menu ; dans l'éditeur de tuile, clic et
   glissé pour peindre (un trait = une annulation), clic droit pipette,
   clic sur la palette, molette pour la couleur. `NHMONEDIT_MOUSE=0`
   coupe la souris.*
3. ✅ **Fait** — **Interface en anglais** **[moyen]** : textes passés
   par `_()` et catalogue anglais, choisis par la locale, comme
   l'éditeur de cartes. *Réalisé : `nhmon_i18n.py` (`NHMONEDIT_LANG`,
   sinon la locale) et `nhmon_i18n_en.py` (environ 680 textes : fiche,
   aide, menus, descriptions des constantes du jeu, vérifications,
   modèles) ; en anglais, l'aperçu des attaques reprend les messages
   anglais du jeu (« The security bot hits! »). Les noms français des
   monstres et ce qui est écrit dans les sources ne sont pas traduits.
   `tests/test_i18n.py` vérifie qu'aucun texte ne manque.*
4. ✅ **Fait** — **Recherche dans la liste** **[facile]** : `/` pour
   aller à un monstre par son nom quand le projet en compte beaucoup.
   *Réalisé : `/` ouvre la liste des monstres, que quelques lettres
   filtrent (nom français, nom anglais, identifiant) ; le filtre de tous
   les menus ignore désormais les accents.*
5. ✅ **Fait** — **Fiche comparée** **[moyen]** : deux monstres côte à
   côte (par exemple un robot et le monstre du jeu dont il s'inspire),
   valeurs différentes en couleur. *Réalisé : `B` choisit un autre
   monstre du projet ou du jeu (le monstre d'origine d'un import est
   proposé d'office), affiche tous les champs plus PV et dégâts, les
   différences marquées ≠ en jaune et comptées dans le titre.*
6. ✅ **Fait** — **Aperçu de l'attaque** **[facile]** : afficher pour
   chaque attaque ses dégâts moyens et le message que le jeu affiche
   (« Le mecha de combat vous frappe ! », « … crache des flammes »).
   *Réalisé : `attack_preview()` reprend les verbes de `hitmsg()` et
   les souffles de `breathwep[]` tels que traduits dans `po/fr.po`
   (« La sentinelle Arasaka frappe ! », « L'androïde crache du feu ! ») ;
   message et moyenne dans la ligne d'aide de l'attaque, résumé et
   dégâts moyens par tour dans le panneau Aperçu.*

## 4. Projets et fichiers

1. ✅ **Fait** — **Fusionner des projets** **[facile]** : importer les
   monstres d'un autre fichier JSON (ce qui règle en partie la limite
   1.4). *Réalisé : menu Projet (`p`), « Fusionner un autre projet… » :
   choix parmi les projets voisins ou chemin saisi ; les monstres
   identiques sont ignorés, les noms déjà pris deviennent « mk II » ;
   une seule annulation défait la fusion. Nouveau module
   `nhmon_project.py`.*
2. ✅ **Fait** — **Exporter un monstre** **[facile]** : un fichier par
   monstre pour l'échanger, et l'import correspondant. *Réalisé : menu
   Projet, « Exporter le monstre… » écrit `<identifiant>.nhmon.json`
   (format `nhmonedit-monstre`), « Importer un monstre exporté… » le
   relit (noms renommés au besoin, doublon exact ignoré) ; la fusion
   accepte aussi ces fichiers.*
3. ✅ **Fait** — **Sauvegarde de secours** **[facile]** : enregistrement
   automatique régulier, comme `*.nhme-autosave` dans l'éditeur de
   cartes. *Réalisé : `projet.json.nhmonedit-autosave` écrit au plus
   une fois par minute tant que le projet est modifié (même sans
   toucher au clavier), proposé au lancement s'il est plus récent que
   le projet, effacé à l'enregistrement et à la sortie.*
4. ✅ **Fait** — **Bibliothèque de modèles personnels** **[moyen]** :
   enregistrer un monstre comme modèle, proposé ensuite par `n` à côté
   des modèles fournis. *Réalisé : menu Projet, « Enregistrer le
   monstre comme modèle… » (nom, description, remplacement confirmé) et
   « Supprimer un modèle personnel… » ; modèles rangés dans
   `~/.config/nhmonedit/modeles.json` (ou `NHMONEDIT_TEMPLATES`),
   communs à tous les projets, marqués « (perso) » dans `n`.*
5. ✅ **Fait** — **Fichier de configuration** **[facile]** : dossier des
   sources, du jeu, options de compilation, projet par défaut, au lieu
   des seules variables d'environnement. *Réalisé : `nhmon_config.py`
   lit `~/.config/nhmonedit/config` (ou `NHMONEDIT_CONFIG`), format INI
   comme l'éditeur de cartes : `[jeu]` sources, répertoire, make ;
   `[editeur]` projet, langue, souris, sauvegarde. Les erreurs
   s'affichent au lancement ; exemple commenté dans `config.exemple`.*

## 5. Intégration avec le jeu

1. ✅ **Fait** — **Lancer le jeu dans tmux** **[moyen]** : comme
   l'éditeur de cartes, ouvrir NetHack dans un panneau à côté de
   l'éditeur et y créer le monstre automatiquement (Ctrl-G et son nom).
   *Réalisé : `nhmon_game.py` ; `j` lance le jeu en mode wizard dans un
   panneau tmux (fenêtre « nethack » si l'écran est étroit, session à
   part hors de tmux), attend qu'il soit prêt et y crée le monstre ;
   tant que la partie tourne, `j` crée le monstre choisi sans relancer.
   Sans tmux, le jeu se lance en plein écran comme avant. Essayé :
   « Un drone de combat apparaît à côté de vous. »*
2. ✅ **Fait** — **Place dans la classe** **[facile]** : choisir après
   quel monstre de la classe insérer le nouveau, au lieu de la fin de la
   classe (l'ordre compte pour les monstres créés « de la même
   classe », par exemple par certains pièges et sorts). *Réalisé :
   champ « Placer après » (menu des monstres du premier bloc de la
   classe avec leur nom français, vide = fin de la classe) ; les
   plages que le code parcourt dans l'ordre (dragons et bébés dragons)
   sont exclues, le champ se vide quand la classe change ; plusieurs
   monstres placés après le même gardent l'ordre du projet, et les
   tuiles suivent.*
3. **Entrée de `doc/fixes5-0-0.txt`** **[facile]** : les conventions du
   jeu demandent de noter les changements visibles ; proposer une ligne
   lors de l'intégration.
4. **Commit dans les sources** **[facile]** : après une intégration
   réussie, proposer un commit git dans les sources, avec la liste des
   monstres ajoutés.
5. **Annuler une intégration** **[facile]** : rétablir les fichiers
   depuis le dernier dossier de `sauvegardes/`.
6. **Sons et phrases propres aux robots** **[gros]** : un son
   `MS_BEEP` ou des répliques de robot (« Veuillez présenter votre
   badge. ») demandent du code dans `src/sounds.c` ; l'éditeur pourrait
   écrire ces répliques à partir d'une liste saisie dans la fiche.

## 6. Robots : nouvelles règles de jeu

Idées qui demandent de modifier le code C du jeu, et non plus seulement
ses tables : à faire dans les sources, puis à proposer dans l'éditeur
sous forme de cases à cocher.

1. **Épave à la destruction** **[moyen]** : comme le golem de fer laisse
   des chaînes, un robot détruit pourrait laisser de la ferraille ou
   des composants (`make_corpse()`, `src/mon.c`).
2. **Faiblesse à l'électricité et à l'eau** **[moyen]** : dégâts doublés
   par les décharges, court-circuit dans l'eau, rouille pour les robots
   en métal (`src/mhitm.c`, `src/trap.c`).
3. **Piratage** **[gros]** : un robot que le Netrunner peut rendre
   pacifique ou apprivoiser, comme on apprivoise un animal.
4. **Une classe « robot » à part** **[gros]** : un symbole propre
   (`include/defsym.h`) au lieu d'emprunter la classe golem, avec son
   entrée dans les jeux de symboles et l'aide du jeu.
5. **Réparation** **[moyen]** : un robot qui se répare en ramassant de
   la ferraille, au lieu de se régénérer comme un être vivant.
6. **Drones en essaim** **[moyen]** : un « drone-mère » qui en fabrique
   d'autres (sur le modèle des reines et des bourdons).

## 7. Relation avec l'éditeur de cartes

1. **Monstres connus de nhmapedit** **[facile]** : ajouter les robots
   intégrés à la liste des monstres de l'éditeur de cartes
   (`nhdata.json`), pour les placer avec `des.monster()` dans un niveau.
2. **Salle de robots** **[moyen]** : modèle de niveau ou de salle à
   thème (usine, entrepôt automatisé) peuplé des robots du projet.
3. **Noms vus en jeu** **[facile]** : l'éditeur de cartes affiche les
   noms du thème cyber ; ceux des nouveaux robots y apparaîtraient après
   compilation de `fr@cyber.mo`, à vérifier.

## 8. Qualité du projet

1. **Tests de l'interface** **[moyen]** : piloter l'éditeur dans tmux
   (création d'un monstre, saisie, intégration sur une copie des
   sources), comme `tests/test_ui.py` de l'éditeur de cartes.
2. **Test de compilation** **[moyen]** : un test lent, facultatif, qui
   intègre les modèles dans une copie des sources, compile et lance
   `tilemap`.
3. **Intégration continue** **[facile]** : tests lancés à chaque
   commit.
4. **Découpage de `nhmonedit.py`** **[facile]** : séparer l'affichage,
   la saisie et les actions sur les sources en modules, comme les
   `nhme_*.py` de l'éditeur de cartes.
