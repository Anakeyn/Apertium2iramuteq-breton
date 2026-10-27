"""
Développe un dictionnaire monolingue Apertium (.dix) en liste de
(forme de surface, analyse) — équivalent simplifié de `lt-expand`.

Seul le sens « analyse » est conservé : les entrées r="RL" (génération
seulement) sont ignorées, les entrées r="LR" (variantes acceptées en
lecture, y compris les mutations et les fautes courantes) sont gardées.
"""
import itertools
import xml.etree.ElementTree as ET

LIMITE_PAR_ENTREE = 20000   # garde-fou contre une explosion combinatoire


class Expanseur:
    def __init__(self, chemin):
        self.racine = ET.parse(chemin).getroot()
        self.pardefs = {p.get("n"): p for p in self.racine.find("pardefs")}
        self._cache = {}

    # ---- contenu d'un <l>, <r> ou <i> -> chaîne -------------------------
    @staticmethod
    def _texte(el, cote):
        """cote = 'l' (surface) ou 'r' (analyse)."""
        morceaux = [el.text or ""]
        for enfant in el:
            t = enfant.tag
            if t == "s":
                morceaux.append(f"<{enfant.get('n')}>" if cote == "r" else "")
            elif t == "b":
                morceaux.append(" ")
            elif t == "j":
                morceaux.append("+")
            elif t == "g":
                # partie invariable d'une locution : texte des deux côtés,
                # repérée par « # » côté analyse
                interne = Expanseur._texte(enfant, cote)
                morceaux.append(("#" + interne + "#") if cote == "r" else interne)
            elif t == "a":
                pass
            morceaux.append(enfant.tail or "")
        return "".join(morceaux)

    # ---- une entrée <e> -> liste de (gauche, droite) ---------------------
    def _entree(self, e):
        if e.get("r") == "RL":
            return []
        parties = []
        for el in e:
            t = el.tag
            if t == "p":
                parties.append([(self._texte(el.find("l"), "l"),
                                 self._texte(el.find("r"), "r"))])
            elif t == "i":
                txt_l = self._texte(el, "l")
                txt_r = self._texte(el, "r")
                parties.append([(txt_l, txt_r)])
            elif t == "par":
                parties.append(self.pardef(el.get("n")))
            elif t == "re":
                return []           # expressions régulières (nombres) : ignorées
        resultats = []
        for combo in itertools.product(*parties):
            resultats.append(("".join(c[0] for c in combo),
                              "".join(c[1] for c in combo)))
            if len(resultats) > LIMITE_PAR_ENTREE:
                break
        return resultats

    def pardef(self, nom):
        if nom not in self._cache:
            self._cache[nom] = []   # protège d'une éventuelle récursion
            res = []
            for e in self.pardefs[nom]:
                res.extend(self._entree(e))
            self._cache[nom] = res
        return self._cache[nom]

    def developper(self, sections=None):
        """Renvoie un itérable de (surface, analyse, id_section)."""
        for sec in self.racine.iter("section"):
            if sections and sec.get("id") not in sections:
                continue
            for e in sec:
                if e.tag != "e":
                    continue
                for gauche, droite in self._entree(e):
                    yield gauche, droite, sec.get("id")


def decouper_analyse(droite):
    """'den<n><m><pl>' -> ('den', ['n','m','pl']) ; gère '#' et '+'."""
    premier = droite.split("+")[0]
    queue = ""
    if "#" in premier:
        morceaux = premier.split("#")
        premier = morceaux[0] + "".join(morceaux[2::2])
        queue = "".join(morceaux[1::2])
    if "<" in premier:
        lemme = premier[:premier.index("<")]
        etiquettes = premier[premier.index("<") + 1:-1].split("><")
    else:
        lemme, etiquettes = premier, []
    return (lemme + queue).strip(), etiquettes
