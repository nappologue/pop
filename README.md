# POP - Plateforme d'Optimisation des Progressions

Une plateforme d'apprentissage continu permettant la gestion de formations, de quiz et le suivi des progrès des apprenants.

## 📋 Description

POP (Plateforme d'Optimisation des Progressions) est une application web développée avec Flask qui offre un environnement complet pour :
- La gestion des formations et contenus pédagogiques
- La création et l'administration de quiz
- Le suivi personnalisé des progressions
- L'authentification sécurisée des utilisateurs

## 🚀 Technologies Utilisées

- **Backend**: Flask 3.0.0, SQLAlchemy, Flask-Login
- **Base de données**: PostgreSQL 15
- **Serveur Web**: Nginx
- **Serveur WSGI**: Gunicorn
- **Conteneurisation**: Docker, Docker Compose
- **SSL/TLS**: Let's Encrypt (Certbot)
- **Gestion de processus**: Supervisor

## 📦 Prérequis

- Docker (version 20.10+)
- Docker Compose (version 2.0+)
- Git

## 🔧 Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/nappologue/pop.git
cd pop
```

### 2. Configuration de l'environnement

Copier le fichier d'exemple et configurer les variables :

```bash
cp .env.example .env
```

Éditer le fichier `.env` et modifier les valeurs suivantes :

```bash
# Changer le mode selon votre environnement
MODE=DEV  # ou PROD pour la production

# Générer une clé secrète forte
SECRET_KEY=votre-cle-secrete-forte-et-aleatoire

# Configurer les identifiants de base de données
POSTGRES_PASSWORD=mot-de-passe-securise

# Pour le mode PROD uniquement
DOMAIN_NAME=votre-domaine.com
LETSENCRYPT_EMAIL=admin@votre-domaine.com
```

### 3. Construction et démarrage des conteneurs

```bash
# Construction des images Docker
docker-compose build

# Démarrage des services
docker-compose up -d
```

### 4. Accès à l'application

- **Mode DEV**: http://localhost
- **Mode PROD**: https://votre-domaine.com

## 🔄 Mode Développement vs Production

### Mode Développement (DEV)
- Utilise HTTP uniquement (port 80)
- Pas de certificats SSL
- Configuration Nginx simplifiée
- Variables d'environnement de développement

### Mode Production (PROD)
- Redirection automatique HTTP → HTTPS
- Certificats SSL Let's Encrypt
- Configuration Nginx sécurisée
- En-têtes de sécurité activés
- HSTS, X-Frame-Options, etc.

## 📁 Structure du Projet

```
pop/
├── app/                    # Application Flask
│   ├── __init__.py        # Factory d'application
│   ├── models/            # Modèles de données
│   ├── routes/            # Routes et blueprints
│   ├── services/          # Logique métier
│   ├── utils/             # Utilitaires
│   └── static/            # Fichiers statiques (CSS, JS, images)
├── templates/             # Templates HTML Jinja2
│   ├── base.html         # Template de base
│   ├── auth/             # Templates d'authentification
│   ├── training/         # Templates de formation
│   ├── quiz/             # Templates de quiz
│   └── admin/            # Templates d'administration
├── nginx/                 # Configuration Nginx
│   ├── nginx.conf        # Configuration de base
│   ├── dev.conf          # Configuration développement
│   └── prod.conf         # Configuration production
├── docker/                # Scripts Docker
│   └── entrypoint.sh     # Script de démarrage
├── migrations/            # Migrations de base de données
├── Dockerfile            # Image Docker de l'application
├── docker-compose.yml    # Orchestration des services
├── requirements.txt      # Dépendances Python
├── supervisord.conf      # Configuration Supervisor
└── .env.example          # Template de configuration
```

## 🛠️ Commandes Utiles

### Gestion des conteneurs

```bash
# Démarrer les services
docker-compose up -d

# Arrêter les services
docker-compose down

# Redémarrer les services
docker-compose restart

# Voir les logs
docker-compose logs -f

# Voir les logs d'un service spécifique
docker-compose logs -f app
docker-compose logs -f postgres
```

### Gestion de la base de données

```bash
# Créer une nouvelle migration
docker-compose exec app flask db migrate -m "Description de la migration"

# Appliquer les migrations
docker-compose exec app flask db upgrade

# Revenir à une migration précédente
docker-compose exec app flask db downgrade

# Voir l'historique des migrations
docker-compose exec app flask db history
```

### Accès aux conteneurs

```bash
# Shell dans le conteneur app
docker-compose exec app bash

# Shell dans le conteneur postgres
docker-compose exec postgres psql -U pop_user -d pop_db

# Commandes Flask
docker-compose exec app flask shell
```

### Maintenance

```bash
# Reconstruire les images
docker-compose build --no-cache

# Nettoyer les volumes (ATTENTION: supprime les données)
docker-compose down -v

# Voir l'utilisation des ressources
docker-compose stats
```

## 🔐 Configuration Initiale

### Création d'un utilisateur administrateur

Après le premier démarrage, créer un compte administrateur :

```bash
docker-compose exec app flask shell
>>> from app import db
>>> from app.models import User
>>> admin = User(username='admin', email='admin@example.com', is_admin=True)
>>> admin.set_password('MotDePasseSecurise')
>>> db.session.add(admin)
>>> db.session.commit()
>>> exit()
```

## 🔒 Notes de Sécurité

1. **Changez toujours** les valeurs par défaut dans `.env` :
   - `SECRET_KEY` : Utilisez une clé aléatoire forte
   - `POSTGRES_PASSWORD` : Utilisez un mot de passe complexe

2. **Mode Production** :
   - Configurez un nom de domaine valide
   - Les certificats SSL sont automatiquement générés via Let's Encrypt
   - Les ports 80 et 443 doivent être ouverts sur votre serveur

3. **Base de données** :
   - Les données sont persistées dans un volume Docker
   - Effectuez des sauvegardes régulières

4. **Fichiers sensibles** :
   - Le fichier `.env` ne doit jamais être commité
   - Les certificats SSL sont gérés automatiquement

## 📝 Développement

Pour contribuer au projet :

1. Créer une branche pour votre fonctionnalité
2. Effectuer vos modifications
3. Tester localement avec `MODE=DEV`
4. Soumettre une pull request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

## 👥 Support

Pour toute question ou problème :
- Ouvrir une issue sur GitHub
- Contacter l'équipe de développement

---

**Note**: Cette application est en développement actif. Consultez régulièrement le dépôt pour les mises à jour.
