#!/usr/bin/env python3
"""
Prépare un texte breton pour IRaMuTeQ avec le dictionnaire lexique_br.txt.

IRaMuTeQ coupe les mots à l'apostrophe : « c'hoari » deviendrait « c » + « hoari ».
Ce script réécrit le trigramme c'h en « c_h » (c_hoari), comme dans le
dictionnaire, et harmonise les autres apostrophes (’ ʼ ‘ -> ').
Par défaut, il sépare aussi les mots à trait d'union (« an den-se » ->
« an den se », « a-raok » -> « a raok ») : le dictionnaire couvre chaque
élément, et l'on évite des milliers de formes composées inconnues.

Usage :
  python3 preparer_corpus_breton.py mon_corpus.txt -o corpus_pret.txt
  python3 preparer_corpus_breton.py mon_corpus.txt -o corpus_pret.txt --windows

Le fichier d'entrée peut être :
  * déjà au format IRaMuTeQ (lignes « **** *variable_modalite ») : seules les
    lignes de texte sont modifiées ;
  * un texte brut : il est alors encadré par une ligne « **** *texte_1 ».
  * --un-texte-par-paragraphe : chaque paragraphe d'un texte brut devient un
    texte IRaMuTeQ (**** *texte_N).
"""
import argparse
import re

APOSTROPHES = "’ʼ‘`"


def normaliser(ligne, couper_tirets=True):
    if couper_tirets:
        ligne = re.sub(r"(?<=\w)-(?=\w)", " ", ligne)
    ligne = re.sub(r"([cC])[" + APOSTROPHES + r"']([hH])", r"\1_\2", ligne)
    ligne = re.sub(r"[" + APOSTROPHES + r"]", "'", ligne)
    ligne = ligne.replace(" ", " ").replace(" ", " ")
    return ligne


def main():
    p = argparse.ArgumentParser(description="Préparation d'un corpus breton pour IRaMuTeQ")
    p.add_argument("entree")
    p.add_argument("-o", "--sortie", default="corpus_breton_iramuteq.txt")
    p.add_argument("--windows", action="store_true", help="écrire en Windows-1252 (CRLF)")
    p.add_argument("--un-texte-par-paragraphe", action="store_true")
    p.add_argument("--garder-tirets", action="store_true",
                   help="ne pas séparer les mots composés à trait d'union")
    a = p.parse_args()

    with open(a.entree, encoding="utf-8-sig") as f:
        lignes = f.read().splitlines()

    deja_formate = any(l.startswith("****") for l in lignes)
    sortie = []
    if deja_formate:
        sortie = [l if l.startswith("****") or l.startswith("-*") else normaliser(l, not a.garder_tirets)
                  for l in lignes]
    elif a.un_texte_par_paragraphe:
        paragraphes = re.split(r"\n\s*\n", "\n".join(lignes))
        n = 0
        for par in paragraphes:
            if par.strip():
                n += 1
                sortie += [f"**** *texte_{n}", normaliser(" ".join(par.split()), not a.garder_tirets), ""]
    else:
        sortie = ["**** *texte_1"] + [normaliser(l, not a.garder_tirets) for l in lignes]

    encodage, fin = ("cp1252", "\r\n") if a.windows else ("utf-8", "\n")
    with open(a.sortie, "w", encoding=encodage, errors="replace", newline=fin) as out:
        out.write("\n".join(sortie) + "\n")
    n_ch = sum(l.count("c_h") + l.count("C_h") + l.count("C_H") for l in sortie)
    print(f"{a.sortie} écrit ({n_ch} « c'h » réécrits en « c_h »).")


if __name__ == "__main__":
    main()
