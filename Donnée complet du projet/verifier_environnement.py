r"""Vérifie que Python et les dépendances d'ANA-STAT.abt sont installés.

Lance ce fichier avec le Python du projet :
    ..\.venv\Scripts\python.exe verifier_environnement.py
ou, depuis VS Code, clique droit > Exécuter le fichier Python.
"""
import importlib
import sys

PAQUETS = {
    "PyQt6": "PyQt6",
    "pandas": "pandas",
    "numpy": "numpy",
    "matplotlib": "matplotlib",
    "scipy": "scipy",
    "scikit-learn": "sklearn",
    "statsmodels": "statsmodels",
    "reportlab": "reportlab",
    "python-pptx": "pptx",
    "python-docx": "docx",
    "bcrypt": "bcrypt",
    "SQLAlchemy": "sqlalchemy",
    "openpyxl": "openpyxl",
    "xlrd": "xlrd",
    "pyreadstat": "pyreadstat",
    "PyMySQL": "pymysql",
    "psycopg2": "psycopg2",
}


def main():
    print("=" * 55)
    print(" Vérification de l'environnement ANA-STAT.abt")
    print("=" * 55)
    print(f"Python : {sys.version.split()[0]}")
    print(f"Exécutable : {sys.executable}")
    print()

    manquants = []

    for nom_affiche, nom_module in PAQUETS.items():
        try:
            module = importlib.import_module(nom_module)
            version = getattr(module, "__version__", "")
            print(f"  [OK]   {nom_affiche:<14} {version}")
        except Exception as erreur:
            print(f"  [MANQUE] {nom_affiche:<12} ({erreur})")
            manquants.append(nom_affiche)

    print()

    if manquants:
        print("Dépendances manquantes :", ", ".join(manquants))
        print("Pour les installer :")
        print("    ..\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt")
        return 1

    print("Environnement prêt : ANA-STAT.abt peut démarrer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
