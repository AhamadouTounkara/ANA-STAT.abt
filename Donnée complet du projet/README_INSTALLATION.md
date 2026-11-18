# Installation et lancement d'ANA-STAT.abt

## Ce qui a été réparé

Les anciens environnements `.venv` avaient été créés avec un Python 3.13 du
Microsoft Store qui n'existe plus sur l'ordinateur. Ils ne pouvaient donc plus
démarrer.

Un nouvel environnement propre a été créé avec **Python 3.14.5** dans :

```
Grand Projet\.venv
```

Toutes les dépendances du projet y sont installées, y compris les formats
Excel, SPSS, SAS, Stata et les bases SQL.

## Lancer le logiciel

### Tester sans se connecter : `ABT.py`

Le fichier **`ABT.py`** est le point d'entrée de test : il ouvre directement
le tableau de bord avec un utilisateur factice (`Utilisateur`,
`Administrateur`), sans passer par l'écran de connexion.

- `main.py` → lancement normal avec connexion
- `ABT.py` → lancement rapide sans connexion, réservé aux tests

Ne pas supprimer `ABT.py` : il sert à vérifier l'interface et les modules
pendant le développement.

### Méthode 1 : double-clic

Double-clique sur :

```
Donnée complet du projet\lancer_ana_stat.bat
```

### Méthode 2 : VS Code

1. Ouvre le dossier `Grand Projet` (ou `Donnée complet du projet`) dans VS Code.
2. L'interpréteur Python doit être `.venv\Scripts\python.exe`.
3. Ouvre `main.py` puis appuie sur **F5** et choisis **ANA-STAT.abt**.

### Méthode 3 : terminal

```powershell
cd "C:\Users\HP\Documents\Projet par défaut\Grand Projet\Donnée complet du projet"
..\.venv\Scripts\python.exe main.py
```

## Vérifier l'environnement

```powershell
cd "C:\Users\HP\Documents\Projet par défaut\Grand Projet\Donnée complet du projet"
..\.venv\Scripts\python.exe verifier_environnement.py
```

Le script affiche `[OK]` pour chaque paquet installé et se termine par
« Environnement prêt ».

## Réinstaller les dépendances

Si l'environnement est supprimé ou doit être recréé :

```powershell
cd "C:\Users\HP\Documents\Projet par défaut\Grand Projet"
uv venv --python "C:\Users\HP\AppData\Local\Programs\Python\Python314\python.exe" .venv
uv pip install --python ".venv\Scripts\python.exe" -r "Donnée complet du projet\requirements.txt"
```

Sans `uv`, avec `pip` classique :

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r "Donnée complet du projet\requirements.txt"
```

## Anciens dossiers à supprimer (facultatif)

Une fois que le nouveau `.venv` fonctionne, ces dossiers ne servent plus à rien
et occupent environ 375 Mo :

- `.venv-ancien-store` (ancien environnement cassé)
- `.venv-1`, `.venv-2`, `.venv-3`, `.venv-4` (autres tentatives cassées)

Garde au moins le nouveau `.venv`.

## Remarque sur les fichiers

Le code se trouve dans `Donnée complet du projet`. Le dossier parent
`Grand Projet` contient l'environnement Python, le plan PowerPoint et les
sauvegardes. Lance toujours le logiciel depuis le dossier du code pour que
`utilisateurs.json` et `journal_actions.txt` soient lus au bon endroit.
