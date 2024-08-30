# Analyseur PingCastle Cloud

## Description

Ce script Python, `parse_pingcastle_cloud.py`, est conçu pour parser les résultats de PingCastle Cloud et les convertir en plusieurs feuilles de calcul Excel pour une analyse plus rapide. Cela facilite la révision rapide des rôles des utilisateurs, des applications et des permissions au sein d'un tenant M365. Plus précisément, le script produit les feuilles Excel suivantes :

- **user_roles** : Décrit les rôles des utilisateurs, en indiquant si l'utilisateur a activé l'Authentification Multifacteur (MFA).
- **apps_summary** : Fournit un résumé des applications dans le tenant M365, y compris les rôles/permissions critiques.
- **apps_permissions** : Détaille les permissions des applications au sein du tenant M365 et indique si elles sont critiques.
- **apps_delegate_permissions** : Détaille les permissions déléguées des applications et indique si elles sont critiques.
- **apps_roles** : Détaille les rôles des applications et indique si ils sont critiques.

## Meta-donnée

- Auteur : [**Adrien DJEBAR**]
- Contact : [[adrien.djebar@proton.me](mailto:adrien.djebar@proton.me)]
- Date de création: [30/04/2024 11:44:32]
- Date de dernière modification: [03/05/2024 18:19:50]

## Installation

Avant d'exécuter le script, assurez-vous que Python est installé sur votre système et installez les paquets nécessaires en utilisant :

```bash
pip install -r requirements.txt
```

## Utilisation

Pour exécuter le script, naviguez jusqu'au répertoire du script dans la ligne de commande et exécutez :

```bash
python parse_pingcastle_cloud.py
```

> 🔎 Par défaut, le script recherchera toutes les occurrences dans le dossier auquel est exécuter le script des fichiers commençant par "pingcastlecloud_" et finissant par ".json"

Il est possible de fournir arguments supplémentaires selon les spécificités du script. Consultez l'aide du script pour plus de détails :

```bash
python parse_pingcastle_cloud.py --help
```

## Notes

- Le script nécessite une entrée au format JSON provenant des rapports PingCastle Cloud.
- Les fichiers Excel générés seront créés dans le même répertoire que le script.
- Assurez-vous d'avoir les permissions pour lire le fichier JSON et écrire dans le système de fichiers local.

## Avertissement

Cet outil est fourni tel quel, et bien que tous les efforts aient été faits pour garantir son efficacité, les créateurs ne sont pas responsables des inexactitudes des données ou des problèmes survenant de l'utilisation de ce script.
