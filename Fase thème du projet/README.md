# Fase thème du projet

Dossier de travail pour l'apparence visuelle d'ANA-STAT.abt : couleurs, maquettes,
captures d'écran et composants graphiques.

## Organisation

| Dossier / fichier | Contenu |
| --- | --- |
| `couleurs.json` | Palette claire et sombre (source de référence) |
| `maquettes/` | Maquettes d'écran, wireframes |
| `captures/` | Captures d'écran de l'application |
| `composants/` | Composants graphiques exportés (icônes, boutons, etc.) |

## Code actif

Le code qui utilise ces couleurs se trouve dans :

- `Donnée complet du projet/Design/couleurs.py`
- `Donnée complet du projet/Design/theme.py`
- `Donnée complet du projet/Design/composants.py`

Si tu modifies `couleurs.json`, pense à reporter les changements dans
`Design/couleurs.py` (ou inversement) pour que l'application reste cohérente.

## Conventions

- Interface et commentaires en français.
- Palette principale : bleu nuit `#14213D`, bleu action `#2563EB`,
  fond `#F5F7FA`, texte `#1F2937`.
- Police : Segoe UI.
- Rayon des coins : 9px.
