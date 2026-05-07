"""Construction d'un nuage de mots au format SVG."""

from collections import Counter
from html import escape
import math
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
        for mot in re.findall(r"[^\W_]+(?:'[^\W_]+)?", titre.lower(), re.UNICODE):
            mot = mot.strip("'")
            if len(mot) > 1 and mot not in MOTS_IGNORES:
                compteur[mot] += 1

    return compteur.most_common(nombre)


def generer_svg(frequences):
    """Construit un SVG de nuage de mots."""
    largeur = 1000
    hauteur = 700
    centre_x = largeur // 2
    centre_y = hauteur // 2
    couleurs = [
        "#7b1fa2",
        "#1565c0",
        "#2e7d32",
        "#c2185b",
        "#00838f",
        "#ef6c00",
        "#5e35b1",
        "#43a047",
    ]
    rotations = [0, 0, 0, -18, 18, -35, 35, 90, -90]

    if not frequences:
        return _svg_vide(largeur, hauteur)

    max_frequence = frequences[0][1]
    min_frequence = frequences[-1][1]
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{largeur}" height="{hauteur}" viewBox="0 0 {largeur} {hauteur}">',
        '<rect width="100%" height="100%" fill="white"/>',
    ]
    boites = []

    for index, (mot, frequence) in enumerate(frequences):
        taille = _taille_police(frequence, min_frequence, max_frequence)
        texte = escape(mot)
        rotation = rotations[index % len(rotations)]
        couleur = couleurs[index % len(couleurs)]
        largeur_mot, hauteur_mot = _dimensions_approximees(texte, taille, rotation)
        position = _trouver_position(
            largeur_mot,
            hauteur_mot,
            centre_x,
            centre_y,
            largeur,
            hauteur,
            boites,
            index,
        )

        if position is None:
            continue

        x, y, boite = position
        boites.append(boite)
        elements.append(
            f'<text x="{x}" y="{y}" text-anchor="middle" dominant-baseline="middle" '
            f'font-family="Arial, sans-serif" font-size="{taille}" font-weight="700" '
            f'fill="{couleur}" transform="rotate({rotation} {x} {y})">{texte}</text>'
        )

    elements.append("</svg>")
    return "\n".join(elements)


def _taille_police(frequence, min_frequence, max_frequence):
    if max_frequence == min_frequence:
        return 34
    rapport = (frequence - min_frequence) / (max_frequence - min_frequence)
    return 16 + int(48 * rapport)


def _dimensions_approximees(texte, taille, rotation):
    largeur = max(24, len(texte) * taille * 0.5)
    hauteur = taille
    if abs(rotation) in {90}:
        return hauteur, largeur
    if rotation:
        diagonale = math.sqrt((largeur * largeur) + (hauteur * hauteur))
        return diagonale * 0.72, diagonale * 0.5
    return largeur, hauteur


def _trouver_position(
    largeur_mot, hauteur_mot, centre_x, centre_y, largeur_svg, hauteur_svg, boites, index
):
    if index == 0:
        boite = _boite(centre_x, centre_y, largeur_mot, hauteur_mot)
        return centre_x, centre_y, boite

    for pas in range(1, 2500):
        angle = pas * 0.48
        rayon = 5 * math.sqrt(pas)
        x = int(centre_x + math.cos(angle) * rayon * 1.18)
        y = int(centre_y + math.sin(angle) * rayon * 0.82)
        boite = _boite(x, y, largeur_mot, hauteur_mot)

        if _dans_svg(boite, largeur_svg, hauteur_svg) and not _collision(boite, boites):
            return x, y, boite

    return None


def _boite(x, y, largeur, hauteur):
    marge = 2
    return (
        x - largeur / 2 - marge,
        y - hauteur / 2 - marge,
        x + largeur / 2 + marge,
        y + hauteur / 2 + marge,
    )


def _dans_svg(boite, largeur, hauteur):
    gauche, haut, droite, bas = boite
    return gauche >= 20 and haut >= 20 and droite <= largeur - 20 and bas <= hauteur - 20


def _collision(boite, boites):
    gauche, haut, droite, bas = boite
    for autre_gauche, autre_haut, autre_droite, autre_bas in boites:
        if not (
            droite < autre_gauche
            or gauche > autre_droite
            or bas < autre_haut
            or haut > autre_bas
        ):
            return True
    return False


def _svg_vide(largeur, hauteur):
    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{largeur}" height="{hauteur}" viewBox="0 0 {largeur} {hauteur}">',
            '<rect width="100%" height="100%" fill="white"/>',
            '<text x="40" y="80" font-family="Arial" font-size="24" fill="#222">Aucun mot trouve</text>',
            "</svg>",
        ]
    )
