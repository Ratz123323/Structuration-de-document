"""Acces a la base MongoDB du projet."""

from datetime import datetime, timezone
import re

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.errors import DuplicateKeyError

from config import (
    COLLECTION_ARTICLES,
    COLLECTION_CONSULTATIONS,
    COLLECTION_SOURCES,
    MONGO_DB_NAME,
    MONGO_HOST,
    MONGO_PORT,
)

DATE_FORMAT = "%Y-%m-%d %H:%M"


class BdMongo:
    """Regroupe la connexion MongoDB et les collections du projet."""

    def __init__(self):
        self.client = MongoClient(MONGO_HOST, MONGO_PORT, serverSelectionTimeoutMS=3000)
        self.db = self.client[MONGO_DB_NAME]
        self.sources = self.db[COLLECTION_SOURCES]
        self.articles = self.db[COLLECTION_ARTICLES]
        self.consultations = self.db[COLLECTION_CONSULTATIONS]

    def creer_index(self):
        """Cree les index utiles aux recherches demandees dans l'enonce."""
        self.sources.create_index([("sitemap_url", ASCENDING)], unique=True)
        self.sources.create_index([("active", ASCENDING)])

        self.articles.create_index([("url", ASCENDING)], unique=True)
        self.articles.create_index(
            [("source_id", ASCENDING), ("date_publication", ASCENDING)]
        )
        self.articles.create_index([("date_publication", ASCENDING)])
        self.articles.create_index([("mots_cles", ASCENDING)])

        self.consultations.create_index([("date_consultation", ASCENDING)])
        self.consultations.create_index([("article_id", ASCENDING)])

    def ajouter_source(self, nom, sitemap_url, frequence_heures):
        """Ajoute un abonnement a un sitemap."""
        document = {
            "nom": nom.strip(),
            "sitemap_url": sitemap_url.strip(),
            "active": True,
            "frequence_heures": int(frequence_heures),
            "date_abonnement": datetime.now(timezone.utc),
            "derniere_recuperation": None,
        }

        try:
            return self.sources.insert_one(document).inserted_id
        except DuplicateKeyError:
            return None

    def lister_sources(self):
        """Retourne les sources abonnees, triees par nom."""
        sources = []
        for source in self.sources.find({}).sort("nom", ASCENDING):
            source["_id"] = str(source["_id"])
            source["date_abonnement"] = _formater_date(source.get("date_abonnement"))
            source["derniere_recuperation"] = _formater_date(
                source.get("derniere_recuperation")
            )
            sources.append(source)
        return sources

    def trouver_source(self, source_id):
        """Retourne une source a partir de son identifiant."""
        return self.sources.find_one({"_id": ObjectId(source_id)})

    def supprimer_source(self, source_id):
        """Supprime un abonnement a partir de son identifiant."""
        resultat = self.sources.delete_one({"_id": ObjectId(source_id)})
        return resultat.deleted_count == 1

    def enregistrer_articles(self, articles):
        """Insere ou met a jour les articles recuperes depuis un sitemap."""
        total = 0
        for article in articles:
            resultat = self.articles.update_one(
                {"url": article["url"]},
                {"$set": article},
                upsert=True,
            )
            if resultat.upserted_id is not None or resultat.modified_count == 1:
                total += 1
        return total

    def marquer_recuperation_source(self, source_id):
        """Enregistre la date de derniere recuperation d'une source."""
        self.sources.update_one(
            {"_id": ObjectId(source_id)},
            {"$set": {"derniere_recuperation": datetime.now(timezone.utc)}},
        )

    def rechercher_articles(self, filtres):
        """Recherche les articles selon les criteres du mode consultation."""
        requete = {}

        source_id = filtres.get("source_id")
        if source_id:
            requete["source_id"] = ObjectId(source_id)

        date_debut = _convertir_date_formulaire(filtres.get("date_debut"))
        date_fin = _convertir_date_formulaire(filtres.get("date_fin"))
        if date_debut or date_fin:
            requete["date_publication"] = {}
            if date_debut:
                requete["date_publication"]["$gte"] = date_debut
            if date_fin:
                requete["date_publication"]["$lte"] = date_fin

        texte = filtres.get("texte", "").strip()
        if texte:
            requete["titre"] = {"$regex": re.escape(texte), "$options": "i"}

        mot_cle = filtres.get("mot_cle", "").strip()
        if mot_cle:
            requete["mots_cles"] = {"$regex": re.escape(mot_cle), "$options": "i"}

        consultation_debut = _convertir_datetime_formulaire(
            filtres.get("consultation_debut")
        )
        consultation_fin = _convertir_datetime_formulaire(
            filtres.get("consultation_fin")
        )
        if consultation_debut or consultation_fin:
            requete_consultation = {}
            if consultation_debut or consultation_fin:
                requete_consultation["date_consultation"] = {}
            if consultation_debut:
                requete_consultation["date_consultation"]["$gte"] = consultation_debut
            if consultation_fin:
                requete_consultation["date_consultation"]["$lte"] = consultation_fin

            article_ids = [
                consultation["article_id"]
                for consultation in self.consultations.find(requete_consultation)
            ]
            requete["_id"] = {"$in": article_ids}

        articles = []
        curseur = self.articles.find(requete).sort("date_publication", DESCENDING)
        for article in curseur.limit(200):
            article["_id"] = str(article["_id"])
            article["source_id"] = str(article["source_id"])
            article["date_publication"] = _formater_date(article.get("date_publication"))
            articles.append(article)

        return articles

    def trouver_article(self, article_id):
        """Retourne un article a partir de son identifiant."""
        return self.articles.find_one({"_id": ObjectId(article_id)})

    def enregistrer_consultation(self, article):
        """Enregistre l'horodatage d'un clic sur un titre."""
        document = {
            "article_id": article["_id"],
            "source_id": article["source_id"],
            "titre": article["titre"],
            "url": article["url"],
            "date_consultation": datetime.now(timezone.utc),
        }
        return self.consultations.insert_one(document).inserted_id

    def titres_pour_nuage(self, date_debut, date_fin):
        """Retourne les titres publies dans une periode donnee."""
        requete = {}
        debut = _convertir_date_formulaire(date_debut)
        fin = _convertir_date_formulaire(date_fin)

        if debut or fin:
            requete["date_publication"] = {}
            if debut:
                requete["date_publication"]["$gte"] = debut
            if fin:
                requete["date_publication"]["$lte"] = fin

        return [article["titre"] for article in self.articles.find(requete, {"titre": 1})]


def get_bd():
    """Retourne un acces a la base MongoDB du projet."""
    return BdMongo()


def _formater_date(valeur):
    if valeur is None:
        return ""
    return valeur.strftime(DATE_FORMAT)


def _convertir_date_formulaire(valeur):
    if not valeur:
        return None
    return datetime.fromisoformat(valeur).replace(tzinfo=timezone.utc)


def _convertir_datetime_formulaire(valeur):
    if not valeur:
        return None
    return datetime.fromisoformat(valeur).replace(tzinfo=timezone.utc)
