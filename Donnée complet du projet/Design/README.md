# Design — couleurs, thème et composants

Ce dossier centralise l'apparence visuelle d'ANA-STAT.abt.

## Contenu

| Fichier | Rôle |
| --- | --- |
| `couleurs.py` | Palettes claire et sombre, police, rayon des coins |
| `theme.py` | Génération de la feuille de style Qt (QSS) et application du thème |
| `composants.py` | Composants d'interface partagés (pied de page, titres de section) |
| `README.md` | Ce guide |

Les fichiers binaires (logo, icônes, images) restent dans le dossier
`Assets/`. L'ancien fichier `Assets/theme.py` est conservé uniquement pour la
compatibilité des anciens imports ; il ne faut plus y ajouter de code.

## Modifier les couleurs

1. Ouvrir `couleurs.py`.
2. Modifier les valeurs de `COULEURS_CLAIR` et/ou `COULEURS_SOMBRE`.
3. Relancer l'application (`ABT.py` pour tester sans connexion, `main.py` pour
   le parcours normal).

Les clés disponibles sont : `bleu_nuit`, `fond`, `fond_widget`, `bleu_action`,
`bleu_action_survol`, `vert_succes`, `orange_avertissement`, `rouge_erreur`,
`texte`, `texte_secondaire` et `bordure`.

## Utiliser le thème

```python
from Design.theme import appliquer_theme, generer_feuille_style

# Appliquer directement à la QApplication
appliquer_theme(app, "clair")   # ou "sombre"

# Ou récupérer la feuille de style pour l'appliquer soi-même
qss = generer_feuille_style("sombre")
```

## Utiliser un composant

```python
from Design.composants import creer_pied_de_page, creer_titre_section

titre = creer_titre_section("Mon titre")
pied = creer_pied_de_page("ANA-STAT.abt v0.1", mode_test=True)
```

Pour ajouter un nouveau composant partagé, l'écrire dans `composants.py` et
l'utiliser depuis les pages concernées.

## Importer l'ancien thème

Les imports existants continuent de fonctionner :

```python
from Assets.theme import generer_feuille_style
```

Mais le code actif est désormais dans `Design/`.
