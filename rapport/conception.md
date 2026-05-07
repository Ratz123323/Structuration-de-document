# Conception

Ce document sert de brouillon pour la partie conception du rapport.

## Exigences retenues depuis l'enonce

L'application doit proposer deux modes :

- mode administration : ajouter un abonnement a un sitemap, supprimer un abonnement, definir une minuterie de recuperation ;
- mode consultation : parcourir les titres d'actualite, filtrer par source, date de publication, texte ou mots-cles, ouvrir un article dans un nouvel onglet ;
- historisation : enregistrer l'horodatage lorsqu'un utilisateur clique sur un titre ;
- nuage de mots : generer, afficher et telecharger un SVG contenant les `n` mots les plus frequents dans les titres pendant une periode donnee.

Contraintes techniques :

- application web Flask ;
- langage Python version 3.8 ou plus ;
- base MongoDB locale avec la connexion `mongodb://localhost:27017` ;
- base de donnees nommee `SD2026_projet` ;
- collections prefixees par `G_AP_`.

## Collections MongoDB

Le cours presente MongoDB comme une base NoSQL orientee documents : une base contient des collections, et une collection contient des documents sous forme cle/valeur proche de JSON. Le projet utilise donc des documents pour representer les sources, les articles et les consultations.

### Collection `G_AP_sources`

Cette collection represente les abonnements aux sources d'actualite.

Document prevu :

```json
{
  "_id": "ObjectId genere par MongoDB",
  "nom": "Le Monde",
  "sitemap_url": "https://www.lemonde.fr/sitemap_news.xml",
  "active": true,
  "frequence_heures": 24,
  "date_abonnement": "date",
  "derniere_recuperation": "date ou null"
}
```

Utilisation :

- afficher les sources abonnees ;
- ajouter ou supprimer un abonnement ;
- savoir quand relancer la recuperation des titres.

### Collection `G_AP_articles`

Cette collection represente les titres recuperes depuis les sitemaps.

Document prevu :

```json
{
  "_id": "ObjectId genere par MongoDB",
  "source_id": "identifiant de la source",
  "source_nom": "Le Monde",
  "titre": "Titre de l'article",
  "url": "https://...",
  "date_publication": "date",
  "mots_cles": ["mot1", "mot2"],
  "date_recuperation": "date"
}
```

Utilisation :

- parcourir les titres globalement ;
- filtrer les titres par source ;
- filtrer les titres par date de publication ;
- chercher dans les titres ou les mots-cles ;
- calculer les frequences de mots pour le nuage SVG.

Le champ `source_nom` reprend le nom de la source dans le document article. Ce choix evite d'avoir besoin d'une jointure pour l'affichage courant, ce qui reste coherent avec le fait que MongoDB n'est pas optimise pour les jointures classiques.

### Collection `G_AP_consultations`

Cette collection represente les clics effectues sur les titres.

Document prevu :

```json
{
  "_id": "ObjectId genere par MongoDB",
  "article_id": "identifiant de l'article",
  "source_id": "identifiant de la source",
  "titre": "Titre de l'article",
  "url": "https://...",
  "date_consultation": "date"
}
```

Utilisation :

- enregistrer l'horodatage du clic ;
- rechercher les articles par date et heure de consultation.

## Index prevus

Le cours indique que les index ameliorent l'efficacite des recherches, avec un cout en insertion et en stockage. Les index sont donc choisis pour les recherches explicitement demandees par l'enonce.

### `G_AP_sources`

- index unique sur `sitemap_url` : eviter deux abonnements identiques ;
- index sur `active` : retrouver les sources actives.

### `G_AP_articles`

- index unique sur `url` : eviter les doublons lors des recuperations successives ;
- index compose sur `source_id` et `date_publication` : recherche par source et periode ;
- index sur `date_publication` : recherche globale par periode ;
- index sur `mots_cles` : recherche par categorie de mots-cles.

### `G_AP_consultations`

- index sur `date_consultation` : recherche par date et heure de consultation ;
- index sur `article_id` : retrouver les consultations d'un article.

## Nuage de mots SVG

Le nuage de mots est construit a partir des titres d'articles sur une periode donnee.

Etapes prevues :

1. selectionner les articles dont `date_publication` est dans l'intervalle choisi ;
2. extraire les mots des titres ;
3. compter les frequences ;
4. conserver les `n` mots les plus frequents ;
5. produire une sortie SVG affichable et telechargeable.

Le parametre `n` doit etre choisi par l'utilisateur, conformement a l'enonce.
