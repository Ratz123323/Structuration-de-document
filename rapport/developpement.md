# Developpement

Ce document sert de brouillon pour la partie developpement du rapport.

## Fonctionnalites realisees

### Mode administration

- ajout d'un abonnement a un sitemap ;
- suppression d'un abonnement ;
- definition d'une frequence de recuperation en heures ;
- recuperation manuelle des articles d'une source abonneee ;
- stockage des titres dans MongoDB.

### Recuperation depuis un sitemap

Le fichier `src/sitemap.py` lit les sitemaps d'actualite au format XML. Pour chaque entree, le projet recupere :

- l'URL de l'article ;
- le titre ;
- la date de publication ;
- les mots-cles lorsqu'ils sont presents ;
- la source associee ;
- la date de recuperation.

Test effectue avec l'exemple de l'enonce :

```text
https://www.lemonde.fr/sitemap_news.xml
```

Resultat du test :

```text
235 articles lus et enregistres dans G_AP_articles.
```

### Mode consultation

La page de consultation permet de parcourir les titres stockes dans MongoDB.

Filtres disponibles :

- source ;
- date de debut ;
- date de fin ;
- texte present dans le titre ;
- mot-cle.

Les articles sont affiches avec leur source, leur date de publication, leur titre cliquable et les mots-cles presents dans le sitemap. L'affichage est limite aux 200 premiers resultats afin de conserver une page consultable.
