# Tutoriel : votre premier robot avec nhmonedit

Ce tutoriel crée pas à pas un monstre pour le NetHack de Night City :
**la sentinelle Arasaka**, un robot de garde rouge qui attend les
intrus et les paralyse d'une décharge. On la règle, on la vérifie, on
l'ajoute aux sources du jeu, puis on la fait apparaître dans une
partie. Comptez vingt minutes, compilation comprise.

Les touches à taper sont indiquées entre crochets : `[n]`, `[Entrée]`…
L'aide complète s'affiche à tout moment avec `[?]`, et la ligne cyan en
bas de l'écran explique le champ sélectionné.

À la fin, la fiche de la sentinelle ressemblera à ceci :

```
' sentinelle Arasaka   (arasaka sentinel)

Niveau 8   Vitesse 10   CA 4   PV 55 fixes   Difficulté 10
Attaque 1  WEAP PHYS 1d8   arme (avec des mains) / physique
Attaque 2  TUCH PLYS 1d4   contact / paralyse (taser)
Drapeaux M3  INFRAVISION, WAITFORU
```

## 1. Lancer l'éditeur

Dans un terminal d'au moins 80 colonnes sur 24 lignes (120 colonnes
pour voir le panneau « Aperçu » à droite), depuis le dossier de
l'éditeur :

```sh
./nhmonedit.sh tutoriel.json
```

`tutoriel.json` est le fichier du projet : il garde vos monstres. Il
n'existe pas encore et sera créé au premier enregistrement. Sans nom de
fichier, l'éditeur ouvre `monstres.json`.

L'éditeur cherche les sources du jeu dans `../NetHack-5.0.0` (sinon :
option `--src`).

L'écran se compose de :

- la **liste des monstres** du projet, à gauche (vide pour l'instant) ;
- la **fiche** du monstre choisi, au centre ;
- le panneau **Aperçu**, à droite si le terminal est assez large :
  difficulté, points de vie, dégâts maximaux, état dans les sources et
  problèmes détectés ;
- en bas, l'aide du champ et la ligne des touches (ou le dernier
  message).

`[Tab]` passe de la liste à la fiche et inversement.

## 2. Partir d'un modèle

Plutôt que de remplir une fiche vide, on part d'un modèle :

1. `[n]` ouvre la liste des modèles. Choisissez **Robot de sécurité**
   (le premier) avec `[Entrée]`. On peut aussi taper quelques lettres
   pour filtrer la liste, par exemple `séc`.
2. L'éditeur demande le **nom français**, celui que le joueur lira dans
   le jeu. Effacez la proposition avec `[Ctrl-U]`, tapez
   `sentinelle Arasaka`, puis `[Entrée]`.
3. Puis le **nom anglais**, le nom interne du jeu (celui qu'on tapera
   pour faire apparaître le monstre). `[Ctrl-U]`, `arasaka sentinel`,
   `[Entrée]`.

Le monstre apparaît dans la liste, précédé de son symbole `'` (la
classe golem). La fiche est sélectionnée, sur le champ « Nom français ».
L'identifiant C a été déduit du nom anglais : `ARASAKA_SENTINEL` (le
jeu le connaîtra sous le nom `PM_ARASAKA_SENTINEL`).

> **Pourquoi la classe golem ?** Les monstres de la classe `'` ont des
> points de vie fixes au lieu d'un tirage de dés, ne respirent pas et
> sont traités par le jeu comme des créatures artificielles : c'est la
> classe naturelle d'un robot. Pour un grand mecha, préférez `H` ; pour
> un drone, `B` ou `e`.

## 3. L'identité

Dans la fiche, `[↑]` et `[↓]` passent d'un champ à l'autre ; `[←]` et
`[→]` changent la valeur ; `[Entrée]` ouvre la saisie complète.

1. **Genre (français)** : `[↓]` une fois, puis `[→]` pour passer à
   « féminin ». Le jeu en a besoin pour accorder ses phrases : « la
   sentinelle Arasaka est détruite ».
2. **Pluriel français** : le champ juste en dessous affiche, en jaune,
   « auto : sentinelles Arasakas (à vérifier) ». Le jeu forme le
   pluriel en ajoutant un « s » à chaque mot (il s'en sert par exemple
   pour « trois sentinelles Arasaka » ou au génocide), et se trompe ici :
   « Arasaka » est un nom propre. Faites `[Entrée]`, effacez le « s »
   final pour obtenir `sentinelles Arasaka`, puis `[Entrée]`. Le
   pluriel corrigé sera écrit dans le catalogue du thème.
3. **Couleur** : descendez jusqu'au champ « Couleur » et faites
   `[Entrée]`. Tapez `rouge` pour filtrer, puis `[Entrée]`. Le symbole
   `'` passe au rouge dans la liste et la fiche.

Les champs « nom anglais masc. / fém. » servent aux monstres dont le
nom change selon le sexe (« dwarf lord » / « dwarf lady ») : laissez-les
vides.

## 4. Les caractéristiques

1. **Niveau** : sur le champ « Niveau » (6), faites `[→]` deux fois pour
   arriver à 8. Regardez le champ « Difficulté » plus bas : il passe de
   8 à 10. L'éditeur la calcule exactement comme le jeu (c'est elle qui
   décide à quelle profondeur le monstre peut apparaître).
2. Laissez la **vitesse** à 10 (un humain va à 12) et la **classe
   d'armure** à 4 (10 = sans armure, plus bas = mieux protégé).
3. **PV fixes (golem)** : 55, c'est raisonnable pour ce niveau (un golem
   de fer en a 120). Pour une valeur précise, `[Entrée]` et tapez-la.

Pour forcer une difficulté à la main, `[Entrée]` sur « Difficulté » ;
une saisie vide revient au calcul automatique.

## 5. Les attaques

Le modèle a deux attaques : une arme (matraque) et une décharge
électrique au contact. Remplaçons la décharge par un taser qui
paralyse :

1. Descendez sur **Attaque 2** et faites `[Entrée]`.
2. Le menu du **type d'attaque** s'ouvre : tapez `contact` et
   `[Entrée]` (AT_TUCH).
3. Le menu des **dégâts** : tapez `paralyse` et `[Entrée]` (AD_PLYS).
4. Les **dés** : `[Ctrl-U]`, tapez `1d4`, `[Entrée]`. « 1d4 » veut dire
   un dé à 4 faces ; pour la paralysie, c'est la durée.

Avec `[←]` et `[→]` sur une attaque, on change le nombre de dés ;
`[Suppr]` vide l'attaque (les suivantes remontent).

## 6. Le comportement

Une sentinelle attend que l'intrus se montre :

1. Descendez sur **Drapeaux M3** et faites `[Entrée]`. Une liste de
   cases à cocher s'ouvre.
2. Placez-vous sur `M3_WAITFORU` (« attend de vous voir ») et cochez
   avec `[Espace]`. `M3_INFRAVISION` est déjà coché : la sentinelle voit
   la chaleur dans le noir.
3. `[Entrée]` valide.

Les autres groupes de drapeaux marchent de même : **M1** pour le corps
(vole, sans mains, blindé…), **M2** pour la nature (hostile, fort,
ramasse les objets…), **G_** pour la génération (unique, en groupes,
sans cadavre…), et les **résistances**.

## 7. L'encyclopédie

Dans le jeu, `;` sur un monstre affiche sa description.

1. Descendez sur **Encyclopédie (fr)**. `[Suppr]` efface le texte du
   modèle, puis `[Entrée]` ouvre l'éditeur de texte.
2. Écrivez votre description, par exemple :

   > Modèle de garde déployé dans les halls d'Arasaka. Elle reste
   > immobile des heures, puis neutralise l'intrus d'une décharge de
   > taser avant d'appeler la sécurité humaine. Qui ne vient jamais.

3. `[Échap]` termine. `[Entrée]` dans le texte commence un nouveau
   paragraphe.

Le champ **Silhouette (tuile)** ne concerne que les versions
graphiques du jeu (Qt, X11) : laissez-le tel quel. Dans le terminal, la
sentinelle est un `'` rouge.

## 8. Vérifier et équilibrer

- Le panneau **Aperçu** affiche « ✔ aucun problème ». Sinon, il liste
  les erreurs (✖, qui bloquent l'intégration) et les avertissements (⚠).
  `[v]` affiche la vérification de tous les monstres du projet.
- `[b]` **compare** la sentinelle aux monstres du jeu de difficulté
  proche, avec leur niveau, vitesse, CA et dégâts maximaux. Une
  difficulté de 10 la met au rang d'un troll ou d'un sergent de
  Militech : prudence pour un personnage débutant.
- `[c]` montre le **code C** qui sera ajouté à `include/monsters.h`,
  les lignes de traduction et l'entrée d'encyclopédie.

Enfin, `[s]` **enregistre** le projet dans `tutoriel.json`. `[u]`
annule la dernière modification, si besoin.

## 9. Ajouter la sentinelle au jeu

1. `[I]` (i majuscule) prépare l'intégration et affiche les
   **différences** fichier par fichier (`+` en vert : ajouté). Parcourez
   avec les flèches, puis `[q]`.
2. L'éditeur demande confirmation en listant les fichiers modifiés.
   `[o]` pour écrire.

L'éditeur a ajouté, dans les sources :

- l'entrée `MON()` de la sentinelle à la fin de la classe golem
  (`include/monsters.h`) ;
- ses 55 PV fixes dans `golemhp()` (`src/makemon.c`) ;
- son nom et son genre en français (`po/fr.po`,
  `po/themes/fr@cyber.po`) ;
- sa description (`dat/data*.base`) et sa tuile
  (`win/share/monsters.txt`).

Une copie des fichiers d'avant est rangée dans `sauvegardes/`. La
ligne du bas indique aussi le nouvel **EDITLEVEL** : la liste des
monstres du jeu a changé, les parties sauvegardées avec l'ancienne
version ne se chargeront plus. Terminez vos parties en cours avant
cette étape.

L'état « Sources » de l'Aperçu passe à « intégré » (pastille ● verte
dans la liste). Si vous modifiez ensuite la sentinelle, il indique
« intégré, modifié depuis » : refaites `[I]`.

> Une intégration met dans les sources **les monstres du projet
> ouvert**, et remplace ceux qu'une intégration précédente y avait
> mis. Gardez donc tous vos monstres dans un même projet.

## 10. Compiler et installer

1. `[m]` lance `make` dans les sources. L'éditeur s'efface pendant la
   compilation, dont on voit la progression ; elle se termine par
   « terminé (code 0) ». `[Entrée]` revient à l'éditeur.
2. `[U]` lance `make update`, qui installe le nouveau jeu dans
   `~/nh/install/games` en gardant votre `sysconf`, vos scores et vos
   sauvegardes (le jeu précédent est gardé sous le nom `nethack.old`).
   Confirmez avec `[o]`.

## 11. Rencontrer la sentinelle

1. `[j]` rappelle la marche à suivre puis lance NetHack en **mode
   wizard** (mode de test : votre nom d'utilisateur doit figurer dans
   la ligne `WIZARDS` du fichier `sysconf` du jeu).
2. Une fois en jeu, faites `[Ctrl-G]`. Le jeu demande quel monstre
   créer : tapez le nom **anglais**, `arasaka sentinel`, et
   `[Entrée]`.
3. Le jeu annonce : « Une sentinelle Arasaka apparaît à côté de vous. »
   Le nom français et le féminin viennent de l'étape 3.
4. Pour lire sa description : `[;]`, déplacez le curseur sur le `'`
   rouge, puis `[.]`.

Si votre personnage ne survit pas au taser, le mode wizard propose de
ne pas mourir : répondez `n` à « Mourir ? ».

En quittant le jeu, `[Entrée]` revient à l'éditeur.

## 12. Aller plus loin

- **Une variante** : `[d]` duplique la sentinelle (« arasaka sentinel
  mk II ») ; montez son niveau et sa CA pour une version d'élite.
- **D'autres robots** : les modèles de `[n]` couvrent drones,
  araignée-robot, androïde, robot recycleur, mechas et tourelle. `[i]`
  importe n'importe quel monstre du jeu comme point de départ.
- **L'ordre** : `[<]` et `[>]` déplacent un monstre dans la liste ;
  deux monstres de la même classe sont ajoutés au jeu dans cet ordre.
- **Retirer** : `[R]` enlève des sources tous les monstres ajoutés par
  l'éditeur et rend les fichiers dans leur état d'origine (puis `[m]`
  et `[U]` pour mettre le jeu à jour). Dans les sources, `git diff`
  montre aussi tout ce qui a changé.
- **Revenir à votre projet** : `./nhmonedit.sh` rouvre `monstres.json`.
  Pensez à y copier la sentinelle si vous voulez la garder avec vos
  autres monstres : une intégration depuis `monstres.json` remplacerait
  sinon celle du tutoriel.

Le [README](README.md) détaille tous les champs, les touches et les
fichiers touchés.
