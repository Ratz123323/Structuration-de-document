"""Construction d'un nuage de mots au format SVG."""

from collections import Counter
from html import escape
import re

MOTS_IGNORES = {
    "a",
    "au",
    "aux",
    "ce",
    "ces",
    "dans",
    "de",
    "des",
    "du",
    "en",
    "et",
    "la",
    "le",
    "les",
    "l",
    "un",
    "une",
}


def mots_frequents(titres, nombre):
    """Retourne les mots les plus frequents dans les titres."""
    compteur = Counter()

    for titre in titres:
        for mot in re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9']+", titre.lower()):
            mot = mot.strip("'")
            if len(mot) > 1 and mot not in MOTS_IGNORES:
                compteur[mot] += 1

    return compteur.most_common(nombre)


def generer_svg(frequences):
    """Construit un SVG simple a partir des frequences de mots."""
    largeur = 900
    hauteur = 500
    marge = 40
    x = marge
    y = 70
    ligne_hauteur = 70

    if not frequences:
        return _svg_vide(largeur, hauteur)

    max_frequence = frequences[0][1]
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{largeur}" height="{hauteur}" viewBox="0 0 {largeur} {hauteur}">',
        '<rect width="100%" height="100%" fill="white"/>',
    ]

    for mot, frequence in frequences:
        taille = 16 + int((frequence / max_frequence) * 44)
        texte = escape(mot)
        estimation_largeur = len(texte) * taille * 0.6

        if x + estimation_largeur > largeur - marge:
            x = marge
            y += ligne_hauteur

        if y > hauteur - marge:
            break

        elements.append(
            f'<text x="{x}" y="{y}" font-family="Arial" font-size="{taille}" fill="#222">{texte}</text>'
        )
        x += int(estimation_largeur) + 28

    elements.append("</svg>")
    return "\n".join(elements)


def _svg_vide(largeur, hauteur):
    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{largeur}" height="{hauteur}" viewBox="0 0 {largeur} {hauteur}">',
            '<rect width="100%" height="100%" fill="white"/>',
            '<text x="40" y="80" font-family="Arial" font-size="24" fill="#222">Aucun mot trouve</text>',
            "</svg>",
        ]
    )
