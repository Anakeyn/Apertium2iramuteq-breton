#!/usr/bin/env python3
"""
Prépare un texte breton pour IRaMuTeQ avec le dictionnaire lexique_br.txt.

IRaMuTeQ coupe les mots à l'apostrophe : « c'hoari » deviendrait « c » + « hoari ».
Ce script réécrit le trigramme c'h en « c_h » (c_hoari), comme dans le
dictionnaire, et harmonise les autres apostrophes (’ ʼ ‘ -> ').
Par défaut, il sépare aussi les mots à trait d'union (« an den-se » ->
« an den se », « a-raok » -> « a raok ») : le dictionnaire couvre chaque
élément, et l'on évite des milliers de formes composées inconnues.
Enfin, il soude les expressions du fichier dictionnaire/expression_br.txt
(« a-benn ma » -> « a_benn_ma », « en doa » -> « en_doa ») en respectant les
limites de mots, ce que ne fait pas le remplacement d'IRaMuTeQ.

Usage :
  python3 preparer_corpus_breton.py mon_corpus.txt -o corpus_pret.txt
  python3 preparer_corpus_breton.py mon_corpus.txt -o corpus_pret.txt --windows
  python3 preparer_corpus_breton.py mon_corpus.txt -o corpus_pret.txt --sans-expressions

Le fichier d'entrée peut être :
  * déjà au format IRaMuTeQ (lignes « **** *variable_modalite ») : seules les
    lignes de texte sont modifiées ;
  * un texte brut : il est alors encadré par une ligne « **** *texte_1 ».
  * --un-texte-par-paragraphe : chaque paragraphe d'un texte brut devient un
    texte IRaMuTeQ (**** *texte_N).
"""
import argparse
import os
import re

APOSTROPHES = "’ʼ‘`"


def normaliser(ligne, couper_tirets=True):
    if couper_tirets:
        ligne = re.sub(r"(?<=\w)-(?=\w)", " ", ligne)
    ligne = re.sub(r"([cC])[" + APOSTROPHES + r"']([hH])", r"\1_\2", ligne)
    ligne = re.sub(r"[" + APOSTROPHES + r"]", "'", ligne)
    ligne = ligne.replace(" ", " ").replace(" ", " ")
    return ligne


class Soudeur:
    """Soude les expressions (mots séparés par des espaces ou un trait d'union)."""

    def __init__(self, chemin):
        self.expressions = {}
        with open(chemin, encoding="utf-8") as f:
            for ligne in f:
                champs = ligne.rstrip("\n\r").split("\t")
                if len(champs) >= 2 and " " in champs[0]:
                    self.expressions[champs[0]] = champs[1]
        self.max_mots = max((len(c.split()) for c in self.expressions), default=0)
        self.nb = 0

    def souder(self, ligne):
        # mots, séparateurs (espaces ou trait d'union seul) et ponctuation
        jetons = re.findall(r"\w+|\s+|[^\w\s]", ligne)
        sortie, i = [], 0
        while i < len(jetons):
            if not re.fullmatch(r"\w+", jetons[i]):
                sortie.append(jetons[i])
                i += 1
                continue
            # positions des mots suivants, séparés par un seul blanc ou tiret
            mots, fins, j = [jetons[i]], [i], i
            while len(mots) < self.max_mots and j + 2 < len(jetons) \
                    and (jetons[j + 1].isspace() or jetons[j + 1] == "-") \
                    and re.fullmatch(r"\w+", jetons[j + 2]):
                j += 2
                mots.append(jetons[j])
                fins.append(j)
            for n in range(len(mots), 1, -1):     # la plus longue d'abord
                soudee = self.expressions.get(" ".join(mots[:n]).lower())
                if soudee:
                    sortie.append(soudee)
                    i = fins[n - 1] + 1
                    self.nb += 1
                    break
            else:
                sortie.append(jetons[i])
                i += 1
        return "".join(sortie)


def trouver_expressions():
    ici = os.path.dirname(os.path.abspath(__file__))
    for chemin in (os.path.join(ici, "dictionnaire", "expression_br.txt"),
                   os.path.join(ici, "expression_br.txt")):
        if os.path.exists(chemin):
            return chemin
    return None


def main():
    p = argparse.ArgumentParser(description="Préparation d'un corpus breton pour IRaMuTeQ")
    p.add_argument("entree")
    p.add_argument("-o", "--sortie", default="corpus_breton_iramuteq.txt")
    p.add_argument("--windows", action="store_true", help="écrire en Windows-1252 (CRLF)")
    p.add_argument("--un-texte-par-paragraphe", action="store_true")
    p.add_argument("--garder-tirets", action="store_true",
                   help="ne pas séparer les mots composés à trait d'union")
    p.add_argument("--expressions", help="fichier d'expressions (défaut : dictionnaire/expression_br.txt)")
    p.add_argument("--sans-expressions", action="store_true", help="ne pas souder les expressions")
    a = p.parse_args()

    soudeur = None
    if not a.sans_expressions:
        chemin = a.expressions or trouver_expressions()
        if chemin:
            soudeur = Soudeur(chemin)
        else:
            print("Fichier d'expressions introuvable : les expressions ne seront pas soudées.")
    tirets = not a.garder_tirets

    def preparer(ligne):
        ligne = normaliser(ligne, tirets)
        return soudeur.souder(ligne) if soudeur else ligne

    with open(a.entree, encoding="utf-8-sig") as f:
        lignes = f.read().splitlines()

    deja_formate = any(l.startswith("****") for l in lignes)
    sortie = []
    if deja_formate:
        sortie = [l if l.startswith("****") or l.startswith("-*") else preparer(l)
                  for l in lignes]
    elif a.un_texte_par_paragraphe:
        paragraphes = re.split(r"\n\s*\n", "\n".join(lignes))
        n = 0
        for par in paragraphes:
            if par.strip():
                n += 1
                sortie += [f"**** *texte_{n}", preparer(" ".join(par.split())), ""]
    else:
        sortie = ["**** *texte_1"] + [preparer(l) for l in lignes]

    encodage, fin = ("cp1252", "\r\n") if a.windows else ("utf-8", "\n")
    with open(a.sortie, "w", encoding=encodage, errors="replace", newline=fin) as out:
        out.write("\n".join(sortie) + "\n")
    n_ch = sum(l.count("c_h") + l.count("C_h") + l.count("C_H") for l in sortie)
    message = f"{a.sortie} écrit ({n_ch} « c'h » réécrits en « c_h »"
    if soudeur:
        message += f", {soudeur.nb} expressions soudées"
    print(message + ").")


if __name__ == "__main__":
    main()
