"""Module Économie — utilise le moteur générique partagé."""
from ModuleGenerique.module_generique import creer_page_module

CATEGORIES_ANALYSES = {
    "Croissance et prix": ["Produit Intérieur Brut (PIB)", "Inflation", "Croissance économique"],
    "Emploi et revenus": ["Emploi", "Chômage", "Revenus des ménages", "Dépenses des ménages"],
    "Consommation et investissement": ["Consommation", "Investissements", "Entreprises"],
    "Commerce": ["Commerce intérieur", "Commerce extérieur", "Importations", "Exportations", "Balance commerciale"],
    "Social": ["Pauvreté", "Inégalités"],
}

INDICATEURS_CONFIG = {
    "Produit Intérieur Brut (PIB)": {"colonnes": ["Catégorie", "PIB"], "famille": "classement",
                                      "mots_cles": {"PIB": ["pib", "gdp"]}},
    "Inflation": {"colonnes": ["Catégorie", "Inflation (%)"], "famille": "classement",
                  "mots_cles": {"Inflation (%)": ["inflation"]}},
    "Croissance économique": {"colonnes": ["Catégorie", "Valeur début", "Valeur fin"], "famille": "taux_evolution",
                               "nom_taux": "Croissance économique (%)",
                               "mots_cles": {"Valeur fin": ["croissance", "pib"]}},
    "Emploi": {"colonnes": ["Catégorie", "Emplois"], "famille": "classement",
               "mots_cles": {"Emplois": ["emploi", "employment"]}},
    "Chômage": {"colonnes": ["Catégorie", "Chômeurs", "Population active"], "famille": "taux",
                "facteur": 100, "nom_taux": "Taux de chômage (%)",
                "mots_cles": {"Chômeurs": ["chomage", "chômage"], "Population active": ["population active"]}},
    "Revenus des ménages": {"colonnes": ["Catégorie", "Revenus"], "famille": "classement",
                             "mots_cles": {"Revenus": ["revenu"]}},
    "Dépenses des ménages": {"colonnes": ["Catégorie", "Dépenses"], "famille": "classement",
                              "mots_cles": {"Dépenses": ["depense", "dépense"]}},
    "Consommation": {"colonnes": ["Catégorie", "Consommation"], "famille": "classement",
                      "mots_cles": {"Consommation": ["consommation"]}},
    "Investissements": {"colonnes": ["Catégorie", "Investissements"], "famille": "classement",
                         "mots_cles": {"Investissements": ["investissement"]}},
    "Entreprises": {"colonnes": ["Catégorie", "Entreprises"], "famille": "classement",
                     "mots_cles": {"Entreprises": ["entreprise"]}},
    "Commerce intérieur": {"colonnes": ["Catégorie", "Commerce intérieur"], "famille": "classement",
                            "mots_cles": {"Commerce intérieur": ["commerce interieur", "commerce intérieur"]}},
    "Commerce extérieur": {"colonnes": ["Catégorie", "Commerce extérieur"], "famille": "classement",
                            "mots_cles": {"Commerce extérieur": ["commerce exterieur", "commerce extérieur"]}},
    "Importations": {"colonnes": ["Catégorie", "Importations"], "famille": "classement",
                      "mots_cles": {"Importations": ["importation"]}},
    "Exportations": {"colonnes": ["Catégorie", "Exportations"], "famille": "classement",
                      "mots_cles": {"Exportations": ["exportation"]}},
    "Balance commerciale": {"colonnes": ["Catégorie", "Exportations", "Importations"], "famille": "solde",
                             "nom_resultat": "Balance commerciale",
                             "mots_cles": {"Exportations": ["exportation"], "Importations": ["importation"]}},
    "Pauvreté": {"colonnes": ["Catégorie", "Taux de pauvreté (%)"], "famille": "classement",
                 "mots_cles": {"Taux de pauvreté (%)": ["pauvrete", "pauvreté"]}},
    "Inégalités": {"colonnes": ["Catégorie", "Indice d'inégalité"], "famille": "classement",
                    "mots_cles": {"Indice d'inégalité": ["inegalite", "inégalité", "gini"]}},
}

SOURCES_SUPPLEMENTAIRES = ["Enquête", "Banque", "Douanes", "API"]

CORRESPONDANCES_FILTRES = {
    "Région": ["region", "région"], "Secteur": ["secteur"], "Entreprise": ["entreprise"],
    "Activité": ["activite", "activité"], "Sexe": ["sexe", "sex"], "Âge": ["age", "âge"],
    "Année": ["annee", "année", "year"], "Période": ["periode", "période"],
}


def creer_page_economie(obtenir_donnees_actuelles, obtenir_domaine_actuel, fonction_import, fonction_import_sql):
    """Assemble la page Économie, avec la même structure que Démographie."""
    return creer_page_module(
        "Économie", CATEGORIES_ANALYSES, INDICATEURS_CONFIG, SOURCES_SUPPLEMENTAIRES,
        CORRESPONDANCES_FILTRES, obtenir_donnees_actuelles, obtenir_domaine_actuel,
        fonction_import, fonction_import_sql
    )