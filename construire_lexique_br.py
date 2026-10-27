#!/usr/bin/env python3
"""
Construit un dictionnaire breton pour IRaMuTeQ (lexique_br.txt) à partir du
dictionnaire morphologique libre d'Apertium (apertium-bre, licence GPL-3).

Usage :
  git clone https://github.com/apertium/apertium-bre.git
  git clone https://github.com/apertium/apertium-br-fr.git      # facultatif
  python3 construire_lexique_br.py apertium-bre/apertium-bre.bre.dix \
          --corpus-annote apertium-br-fr/corpus -o lexique_br.txt

Format produit (celui d'IRaMuTeQ) : une ligne par forme,
  forme <TAB> lemme <TAB> catégorie
avec les catégories d'IRaMuTeQ (nom, ver, aux, adj, adv, pre, con, art_def…).

Conventions :
  * tout est en minuscules ;
  * le trigramme « c'h » est écrit « c_h » (IRaMuTeQ coupe les mots à
    l'apostrophe) : préparez vos textes avec preparer_corpus_breton.py ;
  * les noms propres (np) ne sont pas inclus : IRaMuTeQ les traite comme
    formes non reconnues, comme en français ;
  * une seule analyse par forme (contrainte d'IRaMuTeQ) : on préfère la
    lecture sans mutation, puis les mots-outils, puis nom > verbe > adjectif ;
    les analyses validées à la main du corpus Apertium sont prioritaires.
"""
import argparse
import collections
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from expanseur_dix import Expanseur, decouper_analyse  # noqa: E402

APOSTROPHES = "'’ʼ‘`"
AUXILIAIRES = {"bezañ", "kaout", "endevout"}

PLEINS = {"nom", "ver", "adj", "adv"}

# rang : plus petit = préféré en cas d'ambiguïté
RANG = {"pre": 0, "art_def": 0, "art_ind": 0, "con": 1, "pro_per": 1,
        "pro_dem": 1, "pro_rel": 1, "pro_pos": 1, "pro_ind": 1,
        "adj_pos": 1, "adj_dem": 1, "adj_int": 1, "adj_ind": 1,
        "adv_sup": 2, "aux": 2, "nom": 3, "ver": 4, "adj": 5, "adv": 6,
        "adj_num": 7, "ono": 8}


def majoritaire(compteur):
    """Élément le plus fréquent, départage stable (résultat reproductible)."""
    return max(compteur.items(), key=lambda kv: (kv[1], str(kv[0])))[0]


def normaliser(mot):
    """minuscules, c'h -> c_h, apostrophes isolées retirées."""
    m = mot.lower()
    m = re.sub(r"c[" + APOSTROPHES + r"]h", "c_h", m)
    m = re.sub(r"[" + APOSTROPHES + r"]", "", m)
    return m.strip()


def categorie(etiquettes, lemme, pro_per=True):
    if not etiquettes:
        return None
    t = etiquettes[0]
    s = set(etiquettes[1:])
    if t == "n":
        return "nom"
    if t in ("vblex",):
        return "aux" if lemme in AUXILIAIRES else "ver"
    if t == "vbloc":
        return "aux"
    if t == "adj":
        return "adj"
    if t in ("adv", "preadv"):
        return "adv_sup" if "neg" in s else "adv"
    if t == "pr":
        return "pre"
    if t in ("cnjcoo", "cnjsub", "cnjadv"):
        return "con"
    if t == "det":
        if "def" in s:
            return "art_def"
        if "ind" in s:
            return "art_ind"
        if "pos" in s:
            return "adj_pos"
        if "dem" in s:
            return "adj_dem"
        if "itg" in s:
            return "adj_int"
        return "adj_ind"
    if t == "predet":
        return "adj_ind"
    if t == "num":
        return "adj_num"
    if t == "prn":
        if "dem" in s:
            return "pro_dem"
        if "rel" in s:
            return "pro_rel"
        if "pos" in s:
            return "pro_pos"
        if s & {"subj", "obj", "ref"} and pro_per:
            return "pro_per"
        return "pro_ind"
    if t == "vpart":
        return "adv_sup"           # particules verbales a, e, ez, o
    if t == "ij":
        return "ono"
    return None                    # np, abbr, sym, ponctuation…


def lire_corpus_annote(dossier):
    """Compte (forme, lemme) dans les fichiers *.tag.txt validés à la main."""
    vus = collections.Counter()
    for f in glob.glob(os.path.join(dossier, "**", "*.tag.txt"), recursive=True):
        forme = None
        for ligne in open(f, encoding="utf-8"):
            m = re.match(r'^"<(.+)>"', ligne)
            if m:
                forme = normaliser(m.group(1))
                continue
            m = re.match(r'^\s+"(.+?)"\s+(\S+)', ligne)
            if m and forme:
                vus[(forme, normaliser(m.group(1)), m.group(2))] += 1
                forme = None
    return vus


def main():
    p = argparse.ArgumentParser(description="Apertium -> dictionnaire IRaMuTeQ breton")
    p.add_argument("dix")
    p.add_argument("--corpus-annote", help="dossier corpus d'apertium-br-fr")
    p.add_argument("--sans-pro-per", action="store_true",
                   help="classer les pronoms personnels en pro_ind")
    p.add_argument("-o", "--sortie", default="lexique_br.txt")
    a = p.parse_args()

    analyses = collections.defaultdict(set)   # forme -> {(lemme, cat, mutée, composée)}
    # Morceaux de locutions, ajoutés seulement s'ils manquent : IRaMuTeQ coupe
    # « en doa » en deux mots et peut couper « a-raok » au tiret.
    morceaux = collections.defaultdict(collections.Counter)
    for surface, analyse, _ in Expanseur(a.dix).developper():
        if not surface.strip():
            continue
        lemme_brut, etiq = decouper_analyse(analyse)
        cat = categorie(etiq, lemme_brut, not a.sans_pro_per)
        if not cat:
            continue
        lemme_brut = lemme_brut.replace(" ", "_")      # « memes tra » -> memes_tra
        if " " in surface.strip():
            # « en doa », « hon doa » (kaout) : on garde le dernier mot
            if "#" not in analyse and cat in ("aux", "ver"):
                morceaux[normaliser(surface.split()[-1])][(normaliser(lemme_brut), cat)] += 1
            continue                       # autres locutions : ignorées
        if "-" in surface and cat in ("pre", "adv", "con"):
            # « a-raok », « war-lerc'h », « e-kichen » : dernier élément
            morceaux[normaliser(surface.split("-")[-1])][(normaliser(lemme_brut), cat)] += 1
        forme, lemme = normaliser(surface), normaliser(lemme_brut)
        if (not forme or not re.fullmatch(r"[a-zà-ÿœæ_\-]+", forme)
                or not re.fullmatch(r"[a-zà-ÿœæ_\-]+", lemme)):
            continue
        mutee = forme[:1] != lemme[:1] and not forme.startswith(lemme[:2])
        composee = "+" in analyse
        analyses[forme].add((lemme, cat, mutee, composee))

    gold = lire_corpus_annote(a.corpus_annote) if a.corpus_annote else {}
    gold_par_forme = collections.defaultdict(collections.Counter)
    for (forme, lemme, tag), n in gold.items():
        gold_par_forme[forme][lemme] += n

    # Catégorie dominante de chaque lemme (nombre de formes non mutées) :
    # « ober » est d'abord un verbe, même si le dictionnaire l'admet comme nom.
    dominante = collections.defaultdict(collections.Counter)
    for forme, ens in analyses.items():
        for lemme, cat, mutee, composee in ens:
            if not mutee and not composee:
                dominante[lemme][cat] += 1
    dominante = {l: majoritaire(c) for l, c in dominante.items()}

    choix = {}
    for forme, ens in analyses.items():
        candidats = sorted(ens, key=lambda x: (x[2], x[3],
                                               (x[1] in PLEINS and x[1] != dominante.get(x[0], x[1])),
                                               RANG.get(x[1], 9),
                                               x[0] != forme, x[0], x[1]))
        prefere = gold_par_forme.get(forme)
        if prefere:
            lemme_gold = majoritaire(prefere)
            meilleurs = [c for c in candidats if c[0] == lemme_gold]
            if meilleurs:
                candidats = meilleurs + [c for c in candidats if c not in meilleurs]
        choix[forme] = candidats[0][:2]

    # Contrainte IRaMuTeQ : un lemme = une seule catégorie.
    cats_par_lemme = collections.defaultdict(collections.Counter)
    for lemme, cat in choix.values():
        cats_par_lemme[lemme][cat] += 1
    # Entre mots pleins (nom, verbe, adjectif, adverbe), on aligne la catégorie
    # sur la catégorie majoritaire du lemme ; si un mot-outil partage son lemme
    # avec un mot plein (« e » préposition / « e » particule), on suffixe le
    # lemme du moins fréquent pour les distinguer.
    renommes = harmonises = 0
    for forme, (lemme, cat) in list(choix.items()):
        cat_maj = majoritaire(cats_par_lemme[lemme])
        if cat == cat_maj:
            continue
        if cat in PLEINS and cat_maj in PLEINS:
            choix[forme] = (lemme, cat_maj)
            harmonises += 1
        else:
            choix[forme] = (f"{lemme}_{cat}", cat)
            renommes += 1

    cat_du_lemme = {lemme: cat for lemme, cat in choix.values()}
    ajoutes = 0
    for morceau, compteur in morceaux.items():
        if morceau in choix or len(morceau) < 2 or not re.fullmatch(r"[a-zà-ÿœæ_]+", morceau):
            continue
        # à égalité : graphie standard (war- plutôt que àr-), puis la plus courte
        # (raok -> a-raok plutôt que war-raok)
        (lemme, cat), _ = max(compteur.items(), key=lambda kv: (kv[1], kv[0][0].replace('_', '').isascii(), -len(kv[0][0]), kv[0]))
        cat = cat_du_lemme.setdefault(lemme, cat)
        choix[morceau] = (lemme, cat)
        ajoutes += 1
    print(f"{ajoutes} éléments de locutions ajoutés (raok -> a-raok, doa -> kaout…).")

    with open(a.sortie, "w", encoding="utf-8", newline="\n") as out:
        for forme in sorted(choix):
            lemme, cat = choix[forme]
            out.write(f"{forme}\t{lemme}\t{cat}\n")

    stats = collections.Counter(c for _, c in choix.values())
    ambigues = sum(1 for e in analyses.values() if len({(l, c) for l, c, *_ in e}) > 1)
    print(f"{len(choix)} formes écrites dans {a.sortie} "
          f"({len({l for l, _ in choix.values()})} lemmes).")
    print(f"{ambigues} formes ambiguës résolues, {harmonises} catégories harmonisées "
          f"et {renommes} formes au lemme suffixé (une catégorie par lemme), "
          f"{len(gold_par_forme)} formes tranchées par le corpus annoté.")
    print("Catégories :", ", ".join(f"{c} {n}" for c, n in stats.most_common()))


if __name__ == "__main__":
    main()
