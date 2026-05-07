"""Point d'entree de l'application Flask."""

from flask import Flask, Response, abort, redirect, render_template, request, url_for

from BdMongo import get_bd
from sitemap import recuperer_articles_sitemap
from wordcloud_svg import generer_svg, mots_frequents

app = Flask(__name__)
bd = get_bd()
bd.creer_index()


@app.route("/")
def accueil():
    return redirect(url_for("consultation"))


@app.route("/admin")
def admin():
    sources = bd.lister_sources()
    return render_template("admin.html", sources=sources, erreur=None, message=None)


@app.route("/consultation")
def consultation():
    filtres = {
        "source_id": request.args.get("source_id", ""),
        "date_debut": request.args.get("date_debut", ""),
        "date_fin": request.args.get("date_fin", ""),
        "texte": request.args.get("texte", ""),
        "mot_cle": request.args.get("mot_cle", ""),
        "consultation_debut": request.args.get("consultation_debut", ""),
        "consultation_fin": request.args.get("consultation_fin", ""),
    }
    sources = bd.lister_sources()
    articles = bd.rechercher_articles(filtres)
    return render_template(
        "consultation.html",
        sources=sources,
        articles=articles,
        filtres=filtres,
    )


@app.route("/nuage")
def nuage():
    date_debut = request.args.get("date_debut", "")
    date_fin = request.args.get("date_fin", "")
    nombre = int(request.args.get("nombre", "30") or 30)

    titres = bd.titres_pour_nuage(date_debut, date_fin)
    frequences = mots_frequents(titres, nombre)
    svg = generer_svg(frequences)

    return render_template(
        "wordcloud.html",
        date_debut=date_debut,
        date_fin=date_fin,
        nombre=nombre,
        svg=svg,
        frequences=frequences,
    )


@app.route("/nuage/telecharger")
def telecharger_nuage():
    date_debut = request.args.get("date_debut", "")
    date_fin = request.args.get("date_fin", "")
    nombre = int(request.args.get("nombre", "30") or 30)

    titres = bd.titres_pour_nuage(date_debut, date_fin)
    frequences = mots_frequents(titres, nombre)
    svg = generer_svg(frequences)

    return Response(
        svg,
        mimetype="image/svg+xml",
        headers={"Content-Disposition": "attachment; filename=nuage_mots.svg"},
    )


@app.route("/admin/sources", methods=["POST"])
def ajouter_source():
    nom = request.form.get("nom", "")
    sitemap_url = request.form.get("sitemap_url", "")
    frequence_heures = request.form.get("frequence_heures", "24")

    if not nom.strip() or not sitemap_url.strip():
        sources = bd.lister_sources()
        return render_template(
            "admin.html",
            sources=sources,
            erreur="Le nom et l'URL du sitemap sont obligatoires.",
            message=None,
        )

    source_id = bd.ajouter_source(nom, sitemap_url, frequence_heures)
    if source_id is None:
        sources = bd.lister_sources()
        return render_template(
            "admin.html",
            sources=sources,
            erreur="Ce sitemap est deja abonne.",
            message=None,
        )

    return redirect(url_for("admin"))


@app.route("/admin/sources/<source_id>/supprimer", methods=["POST"])
def supprimer_source(source_id):
    bd.supprimer_source(source_id)
    return redirect(url_for("admin"))


@app.route("/articles/<article_id>/ouvrir")
def ouvrir_article(article_id):
    article = bd.trouver_article(article_id)
    if article is None:
        abort(404)

    bd.enregistrer_consultation(article)
    return redirect(article["url"])


@app.route("/admin/sources/<source_id>/recuperer", methods=["POST"])
def recuperer_source(source_id):
    source = bd.trouver_source(source_id)
    sources = bd.lister_sources()

    if source is None:
        return render_template(
            "admin.html",
            sources=sources,
            erreur="Source introuvable.",
            message=None,
        )

    try:
        articles = recuperer_articles_sitemap(source)
        total = bd.enregistrer_articles(articles)
        bd.marquer_recuperation_source(source_id)
    except Exception as erreur:
        return render_template(
            "admin.html",
            sources=sources,
            erreur=f"Recuperation impossible : {erreur}",
            message=None,
        )

    sources = bd.lister_sources()
    return render_template(
        "admin.html",
        sources=sources,
        erreur=None,
        message=f"{total} article(s) enregistre(s).",
    )


if __name__ == "__main__":
    app.run(debug=False)
