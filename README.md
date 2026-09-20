# Ordinateur — Le Café Virtuel ☕🤖

Bot Discord Python complet pour **Le Café Virtuel**.

## Fonctionnalités

- Économie en Cookies 🍪
- Travail au café avec cooldown
- Café gratuit quotidien
- Boutique et inventaire
- Banque, paiements, récompenses
- XP / niveaux
- Modération avancée
- AutoMod simple (liens, invitations, spam)
- Tickets avec bouton
- Partenariats
- Règles
- Annonces
- Suggestions
- Giveaways persistants
- Statistiques serveur
- Commande `&537UP` pour installer la structure du serveur

## Installation

Python 3.11+ recommandé.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Copie `.env.example` vers `.env`, puis mets ton token :

```env
DISCORD_TOKEN=TON_TOKEN
```

Lance :

```powershell
python bot.py
```

## Important

Dans le Discord Developer Portal, active **Message Content Intent** et **Server Members Intent**.

Le bot doit avoir au minimum les permissions nécessaires à ses commandes (gérer messages, membres, salons, rôles, etc.).

## Setup automatique

Après avoir invité le bot :

```text
&537UP
```

Cette commande crée/configure les catégories et salons principaux du Café Virtuel, dont tickets, partenariats, règles, annonces, giveaways et logs.

La commande `&537UP` nécessite `Administrator`.


## Licence et utilisation

**Tous droits réservés — Reqeuss.**

Ce dépôt est public, mais cela ne signifie pas que son code est librement réutilisable. **Aucune utilisation, copie, modification, redistribution, publication, hébergement, déploiement ou intégration de ce projet, en totalité ou en partie, n'est autorisée sans l'autorisation écrite et officielle préalable de Reqeuss.**

La consultation du code sur GitHub est autorisée. Toute autre utilisation nécessite une autorisation explicite.

Voir le fichier [LICENSE](LICENSE) pour les conditions complètes.
