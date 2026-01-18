# Plateforme ETL d'Intelligence du Marché de l'Emploi

[![Version Python](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)
[![Apache Airflow](https://img.shields.io/badge/Apache%20Airflow-3.1.5-017CEE?logo=apache-airflow)](https://airflow.apache.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-316192?logo=postgresql)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](https://www.docker.com/)
[![Licence](https://img.shields.io/badge/Licence-Apache%202.0-green.svg)](https://opensource.org/licenses/Apache-2.0)

**🌐 Language / Langue:** [English](README.md) | [Français](README.fr.md)

---

Une plateforme complète d'ingénierie des données pour extraire, transformer et charger les données du marché de l'emploi en utilisant Apache Airflow. Ce projet automatise la collecte d'offres d'emploi depuis des APIs externes, les enrichit avec des compétences techniques, des avantages et des données de localisation, et les stocke dans un entrepôt de données dimensionnel pour l'intelligence d'affaires et la visualisation.

## 🏗️ Architecture

```
┌─────────────────┐
│   JSearch API   │
│  Offres d'emploi│
│   externes      │
└────────┬────────┘
         │ Extraction
         ▼
┌─────────────────┐
│ Apache Airflow  │
│  Pipeline ETL   │◄─── Transformation
│  Orchestration  │
└────────┬────────┘
         │ Chargement
         ▼
┌─────────────────┐
│   PostgreSQL    │
│ Entrepôt de     │
│ données (Étoile)│
│ Base distante   │
└────────┬────────┘
         │ Requêtes
         ▼
┌─────────────────┐
│Apache Superset  │
│ Visualisation   │
│ Outil BI distant│
└─────────────────┘
```

### Composants

- **JSearch API** : Source externe de données d'offres d'emploi
- **Apache Airflow** : Moteur d'orchestration pour les workflows ETL
- **PostgreSQL** : Entrepôt de données dimensionnel (schéma en étoile)
- **Apache Superset** : Plateforme d'intelligence d'affaires et de visualisation de données (distant)

### Infrastructure

```
┌──────────────────┐
│   API Externe    │
│  JSearch API     │
│ (Source données) │
└────────┬─────────┘
         │
         │ HTTP/REST
         │ Appels API
         │
         ▼
┌─────────────────────────────────────┐
│          VM 1 (Airflow)             │
│  ┌───────────────────────────────┐  │
│  │   Apache Airflow 3.1.5        │  │
│  │   - Planificateur             │  │
│  │   - Workers (Celery)          │  │
│  │   - Interface Web             │  │
│  │   - Processeur DAG            │  │
│  │   Orchestration ETL           │  │
│  └───────────────────────────────┘  │
└──────────────┬──────────────────────┘
               │
               │ Connexion
               │ PostgreSQL
               │ (Écriture)
               │
               ▼
┌─────────────────────────────────────┐
│   VM 2 (Entrepôt de données)        │
│  ┌───────────────────────────────┐  │
│  │   PostgreSQL 16               │  │
│  │   - Schéma en étoile          │  │
│  │   - Tables de faits           │  │
│  │   - Tables de dimensions      │  │
│  │   Stockage & Gestion          │  │
│  └───────────────────────────────┘  │
└──────────────┬──────────────────────┘
               │
               │ Requêtes SQL
               │ (Lecture)
               │
               ▼
┌─────────────────────────────────────┐
│ VM 3 (Business Intelligence)        │
│  ┌───────────────────────────────┐  │
│  │   Apache Superset             │  │
│  │   - Tableaux de bord          │  │
│  │   - Graphiques & Visus        │  │
│  │   - Analyses & Rapports       │  │
│  │   Exploration des données     │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```


## 📊 Modèle de Données

La plateforme implémente un **schéma en étoile** avec la structure suivante :

```
                           ┌──────────────────┐
                           │    dim_date      │
                           ├──────────────────┤
                           │ date_key (PK)    │
                           │ full_date        │
                           │ year             │
                           │ quarter          │
                           │ month            │
                           │ month_name       │
                           │ day              │
                           │ day_of_week      │
                           │ day_name         │
                           │ week_of_year     │
                           │ is_weekend       │
                           └────────┬─────────┘
                                    │
                                    │
┌──────────────────┐                │               ┌──────────────────┐
│  dim_employer    │                │               │  dim_location    │
├──────────────────┤                │               ├──────────────────┤
│ employer_key (PK)│                │               │ location_key (PK)│
│ employer_name    │                │               │ job_city         │
│ publisher        │                │               │ job_country      │
│ industry         │                │               │ job_region       │
│ company_size     │                │               │ continent        │
│ founded_year     │                │               │ latitude         │
└────────┬─────────┘                │               │ longitude        │
         │                          │               │ postcode         │
         │                          │               │ isocode3166      │
         │                          │               └────────┬─────────┘
         │                          │                        │
         │                          ▼                        │
         │               ┌──────────────────────┐            │
         └──────────────►│  fact_job_post       │◄───────────┘
                         ├──────────────────────┤
                         │ job_key (PK)         │
                         │ date_key (FK)        │
                         │ location_key (FK)    │
                         │ employer_key (FK)    │
                         │ job_id               │
                         │ job_title            │
                         │ apply_link           │
                         │ employment_type      │
                         │ posted_timestamp     │
                         │ job_salary           │
                         │ job_min_salary       │
                         │ job_max_salary       │
                         │ technologies_list    │
                         │ tools_list           │
                         │ benefits_list        │
                         │ seniority_levels_list│
                         │ technology_count     │
                         │ tools_count          │
                         │ benefits_count       │
                         └──────────────────────┘
```

### Table de Faits
- `fact_job_post` : Table de faits centrale contenant les métriques des offres d'emploi et les clés étrangères vers toutes les dimensions

### Tables de Dimensions
- `dim_date` : Dimension temporelle avec hiérarchies (année, trimestre, mois, semaine, jour)
- `dim_location` : Dimension géographique (ville, pays, région, code postal, codes ISO)
- `dim_employer` : Dimension employeur/entreprise avec métadonnées

## 🚀 Fonctionnalités

### Capacités du Pipeline ETL

1. **Extraction**
   - Capteur de vérification de santé de l'API pour garantir la disponibilité de la source de données
   - Récupération automatisée des offres d'emploi depuis l'API JSearch
   - Paramètres de recherche configurables (localisation, plage de dates, nombre de pages)

2. **Transformation**
   - **Détection des Compétences Techniques** : Identifie les technologies et outils mentionnés dans les descriptions d'emploi
     - Paysage Machine Learning & IA (depuis MAD landscape)
     - Langages de programmation et frameworks
     - Outils d'ingénierie des données
   - **Enrichissement de la Localisation** : 
     - Recherche de code postal depuis les données INSEE
     - Génération du code région ISO 3166-2
   - **Extraction du Niveau de Séniorité** : Détecte les exigences d'expérience
   - **Information Salariale** : Extrait les fourchettes salariales mentionnées
   - **Détection des Avantages** : Identifie les avantages comme le télétravail, mutuelle, tickets restaurant, etc.

3. **Chargement**
   - Modélisation dimensionnelle avec clés de substitution
   - Logique d'upsert (gestion des doublons)
   - Maintien de l'intégrité référentielle
   - Gestion des transactions avec rollback en cas d'erreur

## 🛠️ Stack Technologique

- **Orchestration** : Apache Airflow 3.1.5
- **Distribution des Tâches** : Celery avec broker Redis
- **Base de Données** : PostgreSQL 16
- **Visualisation de Données** : Apache Superset (distant)
- **Conteneurisation** : Docker & Docker Compose
- **Langage** : Python 3.13+

## 📁 Structure du Projet

```
job-market-intelligence-etl-platform/
├── dags/
│   └── job_post_dag.py          # Définition du DAG ETL principal
├── data/
│   ├── mad_landscape.json       # Référence outils ML/IA
│   ├── technologies.json        # Référence stack technique
│   └── post_code_insee.csv      # Codes postaux français
├── config/
│   └── airflow.cfg              # Configuration Airflow
├── logs/                         # Logs d'exécution Airflow
├── plugins/                      # Plugins Airflow personnalisés
├── include/                      # Ressources supplémentaires
├── docker-compose.yaml          # Orchestration multi-conteneurs
└── pyproject.toml               # Métadonnées du projet Python
```

## 🔧 Installation et Configuration

### Prérequis

- Docker et Docker Compose
- Au moins 4GB de RAM
- Au moins 2 cœurs CPU
- 10GB d'espace disque libre

### Étapes d'Installation

1. **Cloner le dépôt**
   ```bash
   git clone <repository-url>
   cd job-market-intelligence-etl-platform
   ```

2. **Créer le fichier d'environnement**
   ```bash
   cat > .env << EOF
   AIRFLOW_IMAGE=apache/airflow:3.1.5
   AIRFLOW_UID=50000
   AIRFLOW_PROJ_DIR=.
   
   POSTGRES_USER=airflow
   POSTGRES_PASSWORD=airflow
   POSTGRES_DB=airflow
   POSTGRES_HOST=postgres
   
   _AIRFLOW_WWW_USER_USERNAME=airflow
   _AIRFLOW_WWW_USER_PASSWORD=airflow
   EOF
   ```

3. **Construire et démarrer les services**
   ```bash
   docker-compose up -d
   ```

4. **Accéder à l'interface Airflow**
   - URL : http://localhost:8080
   - Nom d'utilisateur : `airflow`
   - Mot de passe : `airflow`

### Configuration

#### Configurer les Connexions Airflow

1. **Connexion API JSearch** (`jsearch_api`)
   - Type de Conn : HTTP
   - Hôte : `https://jsearch.p.rapidapi.com`
   - Extra (JSON) :
     ```json
     {
       "endpoint": "search",
       "key": "VOTRE_CLE_API",
       "num_page": "1",
       "country": "fr",
       "posted_at": "today"
     }
     ```

2. **Connexion PostgreSQL** (`postgres_job_db`)
   - Type de Conn : Postgres
   - Hôte : `<hote-base-distante>`
   - Schéma : `<nom-base>`
   - Login : `<utilisateur>`
   - Mot de passe : `<mot-de-passe>`
   - Port : `5432`

## 📈 Workflow du DAG

Le `job_post_dag` s'exécute quotidiennement avec la séquence de tâches suivante :

```
┌─────────────────┐
│ is_api_available│
│     @task       │
│    .sensor      │
└────────┬────────┘
         │
         │ L'API est disponible
         │
         ▼
┌─────────────────┐
│    extract      │
│     @task       │
└────────┬────────┘
         │
         │ extraction terminée
         │
         ▼
┌─────────────────┐
│   transform     │
│     @task       │
└────────┬────────┘
         │
         │ transformation terminée
         │
         ▼
┌─────────────────┐
│      load       │
│     @task       │
└─────────────────┘
```

### Détails des Tâches

1. **is_api_available** : Capteur qui vérifie la santé de l'API (intervalles de 60s, timeout de 10min)
2. **extract** : Récupère les offres d'emploi depuis l'API JSearch
3. **transform** : Enrichit les données avec compétences, avantages, codes de localisation
4. **load** : Insère les données dans l'entrepôt de données dimensionnel

### Planification

- **Fréquence** : Quotidienne (`@daily`)
- **Date de Début** : 1er janvier 2026
- **Fuseau Horaire** : Europe/Paris
- **Catchup** : Désactivé
- **Échecs Consécutifs Max** : 3

## 📊 Connexion à Superset

Une fois les données chargées dans PostgreSQL, connectez Apache Superset (distant) pour visualiser les insights :

1. **Ajouter la Base de Données PostgreSQL dans Superset**
   - Naviguer vers Data → Databases → + Database
   - Chaîne de Connexion : `postgresql://<user>:<password>@<host>:<port>/<database>`

2. **Créer les Datasets**
   - Utiliser `fact_job_post` jointure avec les tables de dimensions
   - Configurer les métriques et dimensions

3. **Construire les Tableaux de Bord**
   - Tendances des offres d'emploi dans le temps
   - Technologies les plus demandées
   - Distribution géographique des opportunités
   - Fourchettes salariales par technologie
   - Analyse des avantages

## 🔍 Détails de l'Enrichissement des Données

### Technologies Détectées
- Langages de programmation (Python, Java, SQL, JavaScript, etc.)
- Outils de données (Spark, Kafka, Airflow, dbt, etc.)
- Plateformes Cloud (AWS, Azure, GCP)
- Frameworks ML/IA (TensorFlow, PyTorch, scikit-learn)

### Avantages Identifiés
- Options de télétravail
- Assurance santé (mutuelle)
- Tickets restaurant
- RTT (réduction du temps de travail)
- Primes de performance
- 13ème mois
- Avantages CSE

## 🧪 Tests et Surveillance

### Exécuter Manuellement le DAG
```bash
# Déclencher le DAG manuellement
docker-compose exec airflow-scheduler airflow dags trigger job_post_dag
```

### Voir les Logs
```bash
# Logs du planificateur
docker-compose logs -f airflow-scheduler

# Logs des workers
docker-compose logs -f airflow-worker
```

### Surveiller avec Flower (Interface Celery)
```bash
docker-compose --profile flower up -d
# Accéder à http://localhost:5555
```

## 🛡️ Gestion des Erreurs

- **Échecs API** : Le capteur réessaie pendant 10 minutes avant d'échouer
- **Erreurs de Base de Données** : Les transactions sont annulées en cas d'échec
- **Emplois en Double** : La logique d'upsert empêche les doublons en utilisant `job_id`
- **Échecs Max** : Le DAG se met en pause après 3 exécutions consécutives échouées

## 📝 Développement

### Ajouter de Nouvelles Transformations

Éditez [dags/job_post_dag.py](dags/job_post_dag.py) dans la tâche `transform` pour ajouter une logique personnalisée.

### Étendre les Sources de Données

Ajoutez de nouveaux fichiers de référence dans le répertoire `data/` et mettez à jour la logique de transformation.

### Plugins Airflow Personnalisés

Placez les opérateurs/capteurs personnalisés dans le répertoire `plugins/`.

## 🤝 Contribution

1. Forker le dépôt
2. Créer une branche de fonctionnalité
3. Effectuer vos modifications
4. Tester minutieusement
5. Soumettre une pull request

## 📄 Licence

Apache License 2.0

## 👥 Support

Pour les problèmes, questions ou contributions, veuillez ouvrir une issue dans le dépôt.

---
