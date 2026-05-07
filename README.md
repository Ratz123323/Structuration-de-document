# Structuration de documents

Projet de structuration de documents : nuage de mots d'actualite.

## Equipe

- Kwassi Nyuieva ABOTSI
- Nathan PIERROT

## Conventions du projet

- Base MongoDB : `SD2026_projet`
- Prefixe des collections : `G_AP_`
- Nom du fichier ZIP final : `ABOTSI_PIERROT.zip`
- Application web : Flask
- Connexion MongoDB locale : `mongodb://localhost:27017`

## Organisation des sources

- `src/main.py` : point d'entree de l'application Flask.
- `src/BdMongo.py` : connexion a MongoDB et operations sur les collections.
- `src/config.py` : constantes du projet.
- `src/sitemap.py` : recuperation et lecture des sitemaps d'actualite.
- `src/articles.py` : traitement des titres, dates, sources et consultations.
- `src/wordcloud_svg.py` : calcul des mots frequents et generation du SVG.
