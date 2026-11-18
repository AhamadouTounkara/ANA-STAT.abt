# ANA-STAT.abt

Application desktop PyQt6 d'analyse statistique et démographique, avec cartographie du Mali (SIG),
assistant IA local et génération de rapports.

## Fonctionnalités

- Import de données (Excel, CSV, Stata, SPSS, SAS, SQL)
- Analyses statistiques par domaine (Démographie, Santé, Éducation, Économie, Agriculture, Environnement, Commerce, Emploi/Social, Sécurité)
- Carte choroplèthe du Mali (régions, cercles, communes) avec recherche et export
- Assistant IA local (base de connaissances, analyse automatique, prévision, rapport Word)
- Authentification par rôles (administrateur, analyste, agent de saisie, visiteur)
- Thème clair / sombre
- Export Excel, PDF, Word, PowerPoint, images

## Installation (développement)

```bash
# Depuis "Grand Projet"
uv pip install --python .venv/Scripts/python.exe -r "Donnée complet du projet/requirements.txt"
```

Puis lancer depuis `Donnée complet du projet` :

```bash
# Mode normal (avec connexion)
..\.venv\Scripts\python.exe main.py

# Mode test (sans connexion)
..\.venv\Scripts\python.exe ABT.py
```

Ou double-cliquer sur `lancer_ana_stat.bat` / `lancer_ana_stat_sans_connexion.bat`.

## Structure

```
Grand Projet/
├── .venv/                    Environnement Python (3.14.5)
├── Donnée complet du projet/  Code source de l'application
│   ├── main.py                Entrée normale (connexion)
│   ├── ABT.py                 Entrée de test (sans connexion)
│   ├── Design/                Couleurs, thème Qt, composants
│   ├── Assets/                Logo, icônes
│   ├── IA/                    Module IA
│   ├── SIG/                   Cartographie du Mali
│   └── ... modules sectoriels
├── Fase thème du projet/      Maquettes, captures, couleurs de référence
├── dist/                      Exécutable compilé (ANA-STAT.abt.exe)
└── NOTES_PROJET.md            Notes et conventions du projet
```

## Licence

Usage personnel. Tous droits réservés.
