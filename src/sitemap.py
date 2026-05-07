"""Recuperation et analyse des sitemaps d'actualite."""

from datetime import datetime, timezone
from xml.etree import ElementTree

import requests


def recuperer_articles_sitemap(source):
    """Recupere les articles d'une source a partir de son sitemap."""
    reponse = requests.get(source["sitemap_url"], timeout=10)
    reponse.raise_for_status()

    racine = ElementTree.fromstring(reponse.content)
    articles = []

    for noeud_url in _enfants_par_nom(racine, "url"):
        loc = _texte_premier(noeud_url, "loc")
        titre = _texte_premier(noeud_url, "title")
        date_publication = _texte_premier(noeud_url, "publication_date")
        mots_cles = _texte_premier(noeud_url, "keywords")

        if not loc or not titre:
            continue

        articles.append(
            {
                "source_id": source["_id"],
                "source_nom": source["nom"],
                "titre": titre,
                "url": loc,
                "date_publication": _convertir_date(date_publication),
                "mots_cles": _convertir_mots_cles(mots_cles),
                "date_recuperation": datetime.now(timezone.utc),
            }
        )

    return articles


def _enfants_par_nom(element, nom):
    return [enfant for enfant in element.iter() if _nom_local(enfant.tag) == nom]


def _texte_premier(element, nom):
    for enfant in element.iter():
        if _nom_local(enfant.tag) == nom and enfant.text:
            return enfant.text.strip()
    return ""


def _nom_local(tag):
    return tag.split("}", 1)[-1]


def _convertir_date(valeur):
    if not valeur:
        return None

    try:
        return datetime.fromisoformat(valeur.replace("Z", "+00:00"))
    except ValueError:
        return None


def _convertir_mots_cles(valeur):
    if not valeur:
        return []

    return [mot.strip() for mot in valeur.split(",") if mot.strip()]
