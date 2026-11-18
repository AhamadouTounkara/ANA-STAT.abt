# Notes du projet ANA-STAT.abt

## Règle importante : deux points d'entrée

| Fichier | Usage |
| --- | --- |
| `main.py` | Lancement **normal** : écran de connexion, puis tableau de bord |
| `ABT.py` | Lancement **de test sans connexion** : ouvre directement le tableau de bord avec un utilisateur factice |

**Ne jamais supprimer `ABT.py`.** Il sert à tester l'interface et les modules
sans ressaisir de mot de passe. Quand on teste le logiciel pendant le
développement, on utilise `ABT.py` ; quand on vérifie le parcours réel
utilisateur, on utilise `main.py`.

### Lancer sans connexion (mode test)

Trois méthodes équivalentes :

1. Double-cliquer `lancer_ana_stat_sans_connexion.bat`.
2. Dans VS Code, ouvrir `ABT.py` puis appuyer sur **F5** : la première
   configuration lance le fichier actuellement ouvert.
3. Dans un terminal du dossier `Donnée complet du projet` :
   `..\.venv\Scripts\python.exe ABT.py`.

La fenêtre s'intitule alors **« ANA-STAT.abt — MODE TEST SANS CONNEXION »**.
Si un écran de connexion apparaît, c'est `main.py` qui a été lancé, pas
`ABT.py`.

## Organisation des dossiers

```
Grand Projet\
├── .venv\                        environnement Python (Python 3.14.5)
├── ANA-STAT_plan_du_logiciel.pptx
├── utilisateurs.json             (copie à la racine, non utilisée par le code)
├── Fase thème du projet\         maquettes, captures, couleurs de référence
├── NOTES_PROJET.md               ce fichier
└── Donnée complet du projet\     code source de l'application
    ├── main.py                   entrée normale (connexion)
    ├── ABT.py                    entrée de test (sans connexion)
    ├── requirements.txt
    ├── README_INSTALLATION.md
    ├── verifier_environnement.py
    ├── lancer_ana_stat.bat
    ├── lancer_ana_stat_sans_connexion.bat
    ├── Design\                      couleurs, thème Qt, composants visuels
    ├── Assets\                      logo, icônes, images
    └── ... modules (Démographie, Santé, SIG, IA, etc.)
```

Toujours lancer le code depuis `Donnée complet du projet` : les fichiers
`utilisateurs.json`, `journal_actions.txt` et les sauvegardes sont lus
relativement au dossier courant.

## Environnement

- Python : **3.14.5** (`C:\Users\HP\AppData\Local\Programs\Python\Python314`)
- Environnement virtuel : `Grand Projet\.venv`
- Dépendances : voir `Donnée complet du projet/requirements.txt`
- Vérification : `..\.venv\Scripts\python.exe verifier_environnement.py`
- VS Code : configurations **1. Fichier ouvert (F5)**, **2. ANA-STAT.abt — NORMAL (avec connexion)** et **3. ANA-STAT.abt — TEST (sans connexion, ABT.py)**

Les dossiers `.venv-1` à `.venv-4` et `.venv-ancien-store` sont d'anciennes
tentatives cassées (Python 3.13 du Microsoft Store). Ils peuvent être
supprimés.

## Conventions

- Interface et commentaires en français.
- Le code utilise des imports relatifs au dossier courant ; ne pas déplacer
  les fichiers sans mettre à jour les imports.
- `tableau_bord.py` et `ABT.py` contiennent pour l'instant le même code
  d'interface ; `ABT.py` ajoute seulement le lancement sans connexion à la fin
  et un titre de fenêtre « MODE TEST SANS CONNEXION ». Si l'interface est
  modifiée dans l'un, il faut penser à l'autre.
- Les composants visuels partagés (pied de page, titres de section) sont dans
  `Design/composants.py` ; les couleurs et le thème Qt sont dans
  `Design/couleurs.py` et `Design/theme.py`. `Assets/theme.py` est un shim de
  compatibilité, le code actif est dans `Design/`.
- Les modules sectoriels (Santé, Éducation, etc.) s'appuient sur
  `ModuleGenerique/module_generique.py`.

## Design et apparence

- Code : `Donnée complet du projet/Design/`
- `couleurs.py` : palettes claire et sombre, police, rayon des coins
- `theme.py` : feuille de style Qt (QSS) et `appliquer_theme()`
- `composants.py` : pied de page, titres de section
- `README.md` : comment modifier les couleurs et ajouter un composant
- Les images et icônes restent dans `Assets/`.

## Empaquetage (.exe)

- Outil : PyInstaller 6.22.3 (Python 3.14.5)
- Dossier de sortie : `Grand Projet\dist\ANA-STAT.abt\`
- Exécutable : `ANA-STAT.abt.exe` (mode fenêtré, sans console)
- Les données cartographiques et le logo sont embarqués via `--add-data`.
- Au premier lancement, `utilisateurs.json`, `journal_actions.txt` et
  `sauvegardes_auto\` sont créés à côté de l'exécutable.
- En cas d'erreur au démarrage, un fichier `erreur_ana_stat.log` est écrit à
  côté de l'exécutable.
- Pour reconstruire : lancer PyInstaller depuis `Donnée complet du projet`
  avec `main.py` comme point d'entrée (voir la commande dans l'historique).

## Module IA

- Code : `Donnée complet du projet/IA/module_ia.py`
- Fonctionne en mode local (hors ligne) : base de connaissances, analyse automatique,
  nettoyage, imputation, détection de problèmes, prévision avec incertitude, rapport Word.
- Le fichier `module_ia.py` à la racine du code a été supprimé (doublon obsolète) ;
  seul `IA/module_ia.py` est utilisé.

## Carte du Mali (module SIG)

- Code : `Donnée complet du projet/SIG/sig.py`
- Données locales : `Donnée complet du projet/SIG/donnees_cartes/` (voir le
  `README.md` de ce dossier pour les sources et licences).
- Découpage : **19 régions + district de Bamako**, **160 cercles** (OCHA COD
  2025) et **701 communes** (geoBoundaries 2023).
- Fonctions : carte choroplèthe, détection automatique du niveau et de la
  colonne géographique, reconnaissance des noms et des p-codes, agrégation,
  points GPS, tableau, recherche, exports PNG/PDF/CSV/Excel.
- La carte fonctionne sans connexion Internet. La limite du pays, les régions
  et les cercles sont à jour ; les polygones des communes restent basés sur le
  découpage de 2023.
- Pour un futur empaquetage `.exe`, penser à inclure le dossier
  `SIG/donnees_cartes` dans les données de l'application.

## Prochaines étapes prévues (plan PowerPoint)

1. ~~Cartes du Mali par région, cercle et commune (SIG).~~ **Fait.**
2. Assistant IA en ligne avec clé API (en gardant le mode local).
3. Connexion aux données INSTAT.
4. Empaquetage en `.exe` installable.
