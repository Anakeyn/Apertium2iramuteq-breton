# Apertium2iramuteq-breton

Dictionnaire de lemmatisation du **breton** pour [IRaMuTeQ](https://pratinaud.gitpages.huma-num.fr/iramuteq-website/), construit à partir du dictionnaire morphologique libre d'[Apertium](https://github.com/apertium/apertium-bre) (`apertium-bre`, par Francis Tyers, Fulup Jakez et Gwenvael Jekel, avec le soutien de l'Ofis ar Brezhoneg).

IRaMuTeQ ne propose pas de dictionnaire breton. Sans dictionnaire, les analyses portent sur les formes du texte : *tud*, *dud* et *den* sont trois mots différents. Avec ce dictionnaire, ils sont rattachés au même lemme, *den*.

Le dépôt contient :
- le **dictionnaire prêt à l'emploi** (`dictionnaire/lexique_br.txt`) ;
- un **script de préparation** des textes bretons pour IRaMuTeQ ;
- les **scripts de construction**, pour régénérer le dictionnaire depuis Apertium ;
- un **corpus de test** prêt à ouvrir.

## Sommaire

1. [Le dictionnaire prêt à l'emploi](#1-le-dictionnaire-prêt-à-lemploi--aucune-commande-nécessaire)
2. [Ce que fait le dictionnaire](#2-ce-que-fait-le-dictionnaire)
3. [Préparer ses propres textes](#3-préparer-ses-propres-textes--preparer_corpus_bretonpy)
4. [Installer le dictionnaire dans IRaMuTeQ](#4-installer-le-dictionnaire-dans-iramuteq)
5. [Limites à connaître](#5-limites-à-connaître)
6. [Régénérer le dictionnaire](#6-régénérer-le-dictionnaire)
7. [Licence et citation](#7-licence-et-citation)

## 1. Le dictionnaire prêt à l'emploi : aucune commande nécessaire

| Fichier | Contenu |
|---|---|
| `dictionnaire/lexique_br.txt` | 256 309 formes, 11 837 lemmes, UTF-8, une ligne par forme : `forme<TAB>lemme<TAB>catégorie` |
| `corpus_test/corpus_test_breton.txt` | Corpus de test déjà préparé, UTF-8 (Linux, macOS) |
| `corpus_test/corpus_test_breton_windows.txt` | Le même, en Windows-1252 |

Le corpus de test reprend les 1 164 phrases du corpus d'Apertium, réparties en 47 textes.

**Pour récupérer les fichiers :** sur GitHub, cliquez sur le fichier, puis sur le bouton de téléchargement (*Download raw file*). Vous pouvez aussi récupérer tout le dépôt avec le bouton vert **Code → Download ZIP**.

**Premier essai conseillé :** ouvrez le corpus de test avec ce dictionnaire (voir la [section 4](#4-installer-le-dictionnaire-dans-iramuteq)). Lancez ensuite les *Statistiques textuelles* et regardez combien de formes restent en `nr` (non reconnues) : ce sont surtout des noms propres.

## 2. Ce que fait le dictionnaire

- **Les mutations sont lemmatisées** : *dud*, *tud* → den ; *Wengamp* → Gwengamp ; *zeu* → dont. *c'hoari* muté de *koari* est distingué de *c'hoari* (jouer).
- **Les verbes conjugués** sont rattachés à l'infinitif : *graet* → ober. *eo*, *emañ*, *bet* → bezañ, classé `aux` comme *kaout*, à l'image d'*être* et *avoir* en français.
- **Les prépositions conjuguées** sont rattachées à la préposition : *gantañ* → gant.
- **Les mots-outils** reçoivent les catégories d'IRaMuTeQ : `art_def`, `pre`, `con`, `pro_per`, `adj_pos`… Ils sont donc **supplémentaires** par défaut dans les analyses, comme en français.
- **Les noms propres ne sont pas inclus** : ils restent « non reconnus », comme avec le dictionnaire français.

**Couverture** mesurée sur le corpus de test : **98,9 % des occurrences**. Ce chiffre est optimiste, car ce corpus a servi au développement d'Apertium. Sur un texte contemporain ou dialectal, attendez-vous à moins.

## 3. Préparer ses propres textes : `preparer_corpus_breton.py`

### Pourquoi préparer les textes ?

IRaMuTeQ coupe les mots à l'apostrophe, ce qui casserait le trigramme *c'h* : *c'hoari* deviendrait *c* + *hoari*. Le dictionnaire écrit donc **c_h** (*c_hoari*, *merc_h*), et le texte doit être réécrit de la même façon.

Le script :
1. réécrit *c'h* en *c_h*, quelle que soit l'apostrophe utilisée (' ’ ʼ) ;
2. ramène les autres apostrophes à l'apostrophe droite ;
3. sépare par défaut les mots à trait d'union : *an den-se* → *an den se*, *a-raok* → *a raok*. Le dictionnaire couvre chaque élément.

Il accepte un fichier déjà au format IRaMuTeQ (lignes `****`) ou un texte brut.

### Prérequis

Il faut Python 3.8 ou plus récent, sans aucune bibliothèque à installer.

- **Linux, macOS** : Python est déjà présent ; les commandes s'utilisent telles quelles.
- **Windows** : installez Python depuis [python.org](https://www.python.org/downloads/) en cochant *Add Python to PATH*. Dans les commandes, remplacez `python3` par `python`.

Téléchargez le dépôt (**Code → Download ZIP**), décompressez-le, puis ouvrez un terminal dans ce dossier.

### Commandes

```
python3 preparer_corpus_breton.py mon_texte.txt -o corpus_pret.txt
python3 preparer_corpus_breton.py mon_texte.txt -o corpus_pret.txt --windows
python3 preparer_corpus_breton.py textes_bruts.txt --un-texte-par-paragraphe -o corpus_pret.txt
```

| Option | Effet |
|---|---|
| `-o fichier` | Fichier de sortie |
| `--windows` | Écrit en Windows-1252 avec fins de ligne Windows |
| `--un-texte-par-paragraphe` | Pour un texte brut : chaque paragraphe devient un texte IRaMuTeQ (`**** *texte_N`) |
| `--garder-tirets` | Ne sépare pas les mots à trait d'union |

Les corpus bretons de [wiki2iramuteq](https://github.com/Anakeyn/wiki2iramuteq) sont déjà au format IRaMuTeQ : il suffit de les passer dans ce script.

## 4. Installer le dictionnaire dans IRaMuTeQ

### Méthode A : choisir le dictionnaire à l'ouverture du corpus

Dans la fenêtre de paramètres qui s'affiche avec *Fichier → Ouvrir un corpus* :
1. encodage : **utf-8** (ou **cp1252** pour la version Windows) ;
2. langue : **autre** ;
3. dictionnaire : **Autre**, puis désignez `lexique_br.txt` ;
4. si la case est proposée, décochez **Utiliser le dictionnaire des expressions** : celui d'une autre langue n'a pas de sens pour le breton.

### Méthode B : remplacer le dictionnaire d'une langue inutilisée

À utiliser si votre version ne propose pas le choix du dictionnaire.

1. Les dictionnaires se trouvent dans le dossier `.iramuteq` (ou `.Iramuteq`) de votre dossier personnel, sous-dossier `dictionnaires`.
2. **Sauvegardez** le lexique d'une langue que vous n'utilisez pas.
3. Remplacez-le par `lexique_br.txt`, renommé au même nom.
4. Ouvrez vos corpus bretons en choisissant cette langue, et décochez le dictionnaire des expressions.

Remettez le fichier d'origine en place pour revenir en arrière.

## 5. Limites à connaître

- **Une seule analyse par forme**, c'est une contrainte d'IRaMuTeQ. Pour les formes ambiguës, le script préfère :
  1. la lecture **sans mutation** ;
  2. puis le mot-outil ;
  3. puis la catégorie dominante du lemme.

  Par exemple, *gant* peut être la préposition *gant* (« avec ») ou le nombre *kant* (« cent ») après mutation douce (k → g) : le dictionnaire retient la préposition.

  Environ 12 000 formes sont concernées, et certains choix seront faux en contexte. C'est la limite de toute lemmatisation sans désambiguïsation.
- **Un lemme = une catégorie**, c'est aussi une contrainte d'IRaMuTeQ. Quand un mot-outil et un mot plein partagent un lemme, le moins fréquent reçoit un suffixe. Exemple : *e_adv_sup* pour la particule verbale *e(z)*, à distinguer de la préposition *e*.
- **Catégorie `pro_per`** (pronoms personnels). Si votre IRaMuTeQ ne la connaît pas (fichier `key.cfg`), régénérez le dictionnaire avec `--sans-pro-per` pour les classer en `pro_ind`.
- **Orthographe** : Apertium suit l'orthographe unifiée (*peurunvan*). Les textes en orthographe universitaire, interdialectale ou anciens seront moins bien couverts.

## 6. Régénérer le dictionnaire

Le dictionnaire se reconstruit à partir des dépôts d'Apertium, sans installer Apertium : `expanseur_dix.py` développe lui-même le dictionnaire XML en toutes ses formes fléchies et mutées, à la manière de la commande `lt-expand`.

```
git clone https://github.com/apertium/apertium-bre.git
git clone https://github.com/apertium/apertium-br-fr.git
python3 construire_lexique_br.py apertium-bre/apertium-bre.bre.dix --corpus-annote apertium-br-fr/corpus -o lexique_br.txt
```

Sans `git`, les deux dépôts se téléchargent aussi avec **Code → Download ZIP** sur leurs pages GitHub.

| Fichier | Rôle |
|---|---|
| `expanseur_dix.py` | Développe le dictionnaire Apertium (`.dix`) en couples forme / analyse |
| `construire_lexique_br.py` | Convertit les analyses aux catégories d'IRaMuTeQ, tranche les ambiguïtés et écrit le lexique |

| Option de `construire_lexique_br.py` | Effet |
|---|---|
| `--corpus-annote dossier` | Utilise le corpus annoté à la main d'`apertium-br-fr` pour trancher les ambiguïtés |
| `--sans-pro-per` | Classe les pronoms personnels en `pro_ind` |
| `-o fichier` | Fichier de sortie |

La construction est reproductible : avec les versions ci-dessous, elle redonne exactement le fichier `dictionnaire/lexique_br.txt` du dépôt.

| Source | Version utilisée |
|---|---|
| [apertium-bre](https://github.com/apertium/apertium-bre) | commit `e69f6b6`, 21 juillet 2021 |
| [apertium-br-fr](https://github.com/apertium/apertium-br-fr) | commit `6f0ec11`, 31 mai 2023 |

Pour enrichir le dictionnaire, le plus utile est de contribuer à `apertium-bre`, puis de relancer la construction.

## 7. Licence et citation

`apertium-bre` est distribué sous licence GNU GPL version 3. Ce dictionnaire en est dérivé et est distribué sous la même licence, comme les scripts (voir `LICENSE`).

Pour citer ce travail :

> Rouarch, P. (2026). *Apertium2iramuteq-breton : dictionnaire breton pour IRaMuTeQ à partir d'Apertium*. Anakeyn. https://github.com/Anakeyn/Apertium2iramuteq-breton
