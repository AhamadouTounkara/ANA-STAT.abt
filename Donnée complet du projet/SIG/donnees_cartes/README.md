# Contours administratifs du Mali

Ces fichiers alimentent l'onglet **SIG → Carte du Mali** de ANA-STAT.abt.
Ils sont lus localement : la carte fonctionne sans connexion Internet.

## Fichiers utilisés

| Fichier | Niveau | Source | Licence |
| --- | --- | --- | --- |
| `mali_adm0_2025.geojson` | Limite du pays | OCHA COD Mali 2025 (HDX) | CC BY-IGO |
| `mali_adm1_2025.geojson` | 19 régions + district de Bamako | OCHA COD Mali 2025 (HDX) | CC BY-IGO |
| `mali_adm2_2025.geojson` | 160 cercles | OCHA COD Mali 2025 (HDX) | CC BY-IGO |
| `mali_adm3_2023.geojson` | 701 communes | geoBoundaries gbOpen MLI ADM3 (2023) | CC BY 4.0 |

Les noms et les codes administratifs (`ML01`, etc.) sont reconnus par le
module. Les accents, les tirets et les majuscules sont ignorés lors de la
correspondance avec les fichiers importés.

## Précisions

- Le découpage des régions et des cercles suit la réforme administrative
  malienne de 2023 : **19 régions + le district de Bamako**, et **160 cercles**
  (source COD, version `v03`, valide au 4 septembre 2025).
- Les polygones des **communes** proviennent encore de geoBoundaries 2023
  (701 communes). C'est la source libre la plus complète disponible pour ce
  niveau ; elle n'intègre pas les nouveaux découpages de régions/cercles.
- Certains noms de communes existent dans plusieurs cercles (`Baye`, `Somo`,
  `Benkadi`, `Farako`, etc.). L'application les regroupe sous le même nom et
  l'indique dans le détail de la zone sélectionnée. Pour lever l'ambiguïté, il
  faut fournir une colonne de code administratif ou un couple
  région + cercle + commune.
- Le dossier `archive_ancien_decoupage/` contient les anciens contours
  geoBoundaries (9 régions, 50 cercles, 701 communes). Il n'est plus utilisé.

## Sources

- OCHA COD Mali : <https://data.humdata.org/dataset/cod-ab-mli>
  (jeu de données `Mali - Subnational Administrative Boundaries`, mise à jour
  du 2 avril 2026).
- geoBoundaries : <https://www.geoboundaries.org/>
  (`MLI`, niveau `ADM3`, release 2023, géométrie simplifiée).

## Régénérer les fichiers

Les fichiers ont été allégés (propriétés limitées au nom et au code, coordonnées
arrondies à 5 décimales). Pour les régénérer, repartir des GeoJSON sources
téléchargés depuis les liens ci-dessus, puis conserver les propriétés
`shapeName` et `shapeCode`.
