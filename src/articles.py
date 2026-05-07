"""Traitement des articles d'actualite et des consultations."""

from datetime import datetime, timedelta, timezone

from sitemap import recuperer_articles_sitemap


def recuperer_articles_source(bd, source):
    """Recupere et enregistre les articles d'une source."""
    articles = recuperer_articles_sitemap(source)
    total = bd.enregistrer_articles(articles)
    bd.marquer_recuperation_source(str(source["_id"]))
    return total


def source_a_recuperer(source, maintenant=None):
    """Indique si une source doit etre recuperee selon sa frequence."""
    if maintenant is None:
        maintenant = datetime.now(timezone.utc)

    derniere = source.get("derniere_recuperation")
    if derniere is None:
        return True
    if derniere.tzinfo is None:
        derniere = derniere.replace(tzinfo=timezone.utc)

    frequence = timedelta(hours=int(source.get("frequence_heures", 24)))
    return derniere + frequence <= maintenant


def recuperer_sources_dues(bd):
    """Recupere les sources dont la minuterie est arrivee a echeance."""
    bilan = []

    for source in bd.sources.find({"active": True}):
        if not source_a_recuperer(source):
            continue

        try:
            total = recuperer_articles_source(bd, source)
            bilan.append((source["nom"], total, None))
        except Exception as erreur:
            bilan.append((source["nom"], 0, str(erreur)))

    return bilan
