"""Recuperation et analyse des sitemaps d'actualite."""

from datetime import datetime, timezone
import re
from urllib.parse import urlparse
from xml.etree import ElementTree

import requests

MAX_SITEMAPS_INDEX = 10
MAX_ARTICLES_PAR_SOURCE = 300


def recuperer_articles_sitemap(source):
    """Recupere les articles d'une source a partir de son sitemap."""
    articles = []

    for sitemap_url in _urls_sitemap_possibles(source["sitemap_url"]):
        try:
            racine = _charger_xml(sitemap_url)
        except Exception:
            continue

        articles.extend(_extraire_articles(racine, source))
        if articles:
            break

        for sous_sitemap in _sitemaps_index(racine):
            try:
                racine_sous_sitemap = _charger_xml(sous_sitemap)
            except Exception:
                continue
            articles.extend(_extraire_articles(racine_sous_sitemap, source))
            if len(articles) >= MAX_ARTICLES_PAR_SOURCE:
                return articles[:MAX_ARTICLES_PAR_SOURCE]

        if articles:
            break

    return articles[:MAX_ARTICLES_PAR_SOURCE]


def _charger_xml(url):
    reponse = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
    reponse.raise_for_status()
    return ElementTree.fromstring(reponse.content)


def _urls_sitemap_possibles(url):
    url = url.strip()
    yield url

    parsed = urlparse(url)
    if parsed.scheme and parsed.netloc and not parsed.path.strip("/").endswith(".xml"):
        base = f"{parsed.scheme}://{parsed.netloc}"
        yield f"{base}/sitemap_news.xml"
        yield f"{base}/sitemap-news.xml"
        yield f"{base}/sitemap.xml"


def _sitemaps_index(racine):
    urls = []
    for noeud_sitemap in _enfants_par_nom(racine, "sitemap"):
        loc = _texte_premier(noeud_sitemap, "loc")
        if loc:
            urls.append(loc)

    urls_news = [url for url in urls if "news" in url.lower()]
    return (urls_news or urls)[:MAX_SITEMAPS_INDEX]


def _extraire_articles(racine, source):
    articles = []

    for noeud_url in _enfants_par_nom(racine, "url"):
        loc = _texte_premier(noeud_url, "loc")
        titre = _texte_premier(noeud_url, "title") or _titre_depuis_url(loc)
        date_publication = _texte_premier(noeud_url, "publication_date")
        date_publication = date_publication or _texte_premier(noeud_url, "lastmod")
        mots_cles = _texte_premier(noeud_url, "keywords")
        image_url = _image_depuis_noeud(noeud_url)
        if not image_url:
            image_url = _image_depuis_article(loc)

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
                "image_url": image_url,
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


def _image_depuis_noeud(noeud_url):
    for enfant in noeud_url.iter():
        if _nom_local(enfant.tag) == "loc" and "image" in enfant.tag.lower():
            if enfant.text:
                return enfant.text.strip()
    return ""


def _image_depuis_article(url):
    try:
        reponse = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        reponse.raise_for_status()
    except Exception:
        return ""

    html = reponse.text
    motifs = [
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image["\']',
    ]
    for motif in motifs:
        resultat = re.search(motif, html, re.IGNORECASE)
        if resultat:
            return resultat.group(1).strip()
    return ""


def _titre_depuis_url(url):
    if not url:
        return ""

    chemin = urlparse(url).path.strip("/")
    if not chemin:
        return ""

    dernier_segment = chemin.split("/")[-1]
    dernier_segment = dernier_segment.rsplit(".", 1)[0]
    titre = dernier_segment.replace("-", " ").replace("_", " ").strip()
    return titre[:1].upper() + titre[1:]
