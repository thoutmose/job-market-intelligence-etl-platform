# Job Market Intelligence ETL Platform

[![Python Version](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)
[![Apache Airflow](https://img.shields.io/badge/Apache%20Airflow-3.1.5-017CEE?logo=apache-airflow)](https://airflow.apache.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-316192?logo=postgresql)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](https://opensource.org/licenses/Apache-2.0)

**🌐 Language / Langue:** [English](README.md) | [Français](README.fr.md)

---

A comprehensive data engineering platform for extracting, transforming, and loading job market data using Apache Airflow. This project automates the collection of job postings from external APIs, enriches them with technical skills, benefits, and location data, and stores them in a dimensional data warehouse for business intelligence and visualization.

## 🏗️ Architecture

```
┌─────────────────┐
│   JSearch API   │
│  External Job   │
│   Data Source   │
└────────┬────────┘
         │ Extract
         ▼
┌─────────────────┐
│ Apache Airflow  │
│  ETL Pipeline   │◄─── Transform
│  Orchestration  │
└────────┬────────┘
         │ Load
         ▼
┌─────────────────┐
│   PostgreSQL    │
│ Data Warehouse  │
│ (Star Schema)   │
│ Remote Database │
└────────┬────────┘
         │ Query
         ▼
┌─────────────────┐
│Apache Superset  │
│ Visualization   │
│  Remote BI Tool │
└─────────────────┘
```

### Components

- **JSearch API**: External job posting data source
- **Apache Airflow**: Orchestration engine for ETL workflows
- **PostgreSQL**: Dimensional data warehouse (star schema)
- **Apache Superset**: Business intelligence and data visualization platform (remote)

### Infrastructure

The platform is deployed across three virtual machines:

```
┌────────────────────────────────────────────────────────────────────┐
│                         VM 1: Airflow Server                       │
│                     (Orchestration & Workflow)                     │
├────────────────────────────────────────────────────────────────────┤
│  • Apache Airflow (webserver, scheduler, workers)                  │
│  • DAG Repository                                                  │
│  • Python ETL Scripts                                              │
│  • Docker Containers                                               │
│  • Connects to: JSearch API, PostgreSQL (VM2), Superset (VM3)      │
└────────────────┬───────────────────────────────────────────────────┘
                 │
                 │ Extract, Transform, Load
                 ▼
┌────────────────────────────────────────────────────────────────────┐
│                       VM 2: PostgreSQL Server                      │
│                         (Data Warehouse)                           │
├────────────────────────────────────────────────────────────────────┤
│  • PostgreSQL 16 Database                                          │
│  • Star Schema (fact_job_post + dimensions)                        │
│  • Job posting data storage                                        │
│  • Serves data to: Airflow (VM1), Superset (VM3)                   │
└────────────────────────────────────────────────────────────────────┘
                 │
                 │ Query & Visualize
                 ▼
┌────────────────────────────────────────────────────────────────────┐
│                     VM 3: Apache Superset Server                   │
│                    (BI & Visualization Layer)                      │
├────────────────────────────────────────────────────────────────────┤
│  • Apache Superset Dashboard                                       │
│  • Interactive Charts & Reports                                    │
│  • SQL Lab for Ad-hoc Analysis                                     │
│  • Reads data from: PostgreSQL (VM2)                               │
└────────────────────────────────────────────────────────────────────┘
```

**Infrastructure Details:**
- **VM 1 (Airflow)**: Orchestrates ETL workflows, extracts data from JSearch API, transforms and loads to PostgreSQL
- **VM 2 (PostgreSQL)**: Centralized data warehouse with dimensional model (star schema)
- **VM 3 (Superset)**: Business intelligence platform for data exploration and visualization

## 📊 Data Model

The platform implements a **star schema** with the following structure:

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

### Fact Table
- `fact_job_post`: Central fact table containing job posting metrics and foreign keys to all dimensions

### Dimension Tables
- `dim_date`: Time dimension with hierarchies (year, quarter, month, week, day)
- `dim_location`: Geographic dimension (city, country, region, postal code, ISO codes)
- `dim_employer`: Employer/company dimension with metadata

## 🚀 Features

### ETL Pipeline Capabilities

1. **Extraction**
   - API health check sensor to ensure data source availability
   - Automated job posting retrieval from JSearch API
   - Configurable search parameters (location, date range, number of pages)

2. **Transformation**
   - **Hard Skills Detection**: Identifies technologies and tools mentioned in job descriptions
     - Machine Learning & AI landscape (from MAD landscape)
     - Programming languages and frameworks
     - Data engineering tools
   - **Location Enrichment**: 
     - Postal code lookup from INSEE data
     - ISO 3166-2 region code generation
   - **Seniority Level Extraction**: Detects experience requirements
   - **Salary Information**: Extracts mentioned salary ranges
   - **Benefits Detection**: Identifies perks like remote work, health insurance, meal vouchers, etc.

3. **Loading**
   - Dimensional modeling with surrogate keys
   - Upsert logic (handles duplicates)
   - Referential integrity maintenance
   - Transaction management with rollback on errors

## 🛠️ Technology Stack

- **Orchestration**: Apache Airflow 3.1.5
- **Task Distribution**: Celery with Redis broker
- **Database**: PostgreSQL 16
- **Data Visualization**: Apache Superset (remote)
- **Containerization**: Docker & Docker Compose
- **Language**: Python 3.13+

## 📁 Project Structure

```
job-market-intelligence-etl-platform/
├── dags/
│   └── job_post_dag.py          # Main ETL DAG definition
├── data/
│   ├── mad_landscape.json       # ML/AI tools reference
│   ├── technologies.json        # Tech stack reference
│   └── post_code_insee.csv      # French postal codes
├── config/
│   └── airflow.cfg              # Airflow configuration
├── logs/                         # Airflow execution logs
├── plugins/                      # Custom Airflow plugins
├── include/                      # Additional resources
├── docker-compose.yaml          # Multi-container orchestration
└── pyproject.toml               # Python project metadata
```

## 🔧 Setup and Installation

### Prerequisites

- Docker and Docker Compose
- At least 4GB RAM
- At least 2 CPU cores
- 10GB free disk space

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/thoutmose/job-market-intelligence-etl-platform
   cd job-market-intelligence-etl-platform
   ```

2. **Create environment file**
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

3. **Build and start services**
   ```bash
   docker-compose up -d
   ```

4. **Access Airflow UI**
   - URL: http://localhost:8080
   - Username: `airflow`
   - Password: `airflow`

### Configuration

#### Set up Airflow Connections

1. **JSearch API Connection** (`jsearch_api`)
   - Conn Type: HTTP
   - Host: `https://jsearch.p.rapidapi.com`
   - Extra (JSON):
     ```json
     {
       "endpoint": "search",
       "key": "YOUR_API_KEY",
       "num_page": "1",
       "country": "fr",
       "posted_at": "today"
     }
     ```

2. **PostgreSQL Connection** (`postgres_job_db`)
   - Conn Type: Postgres
   - Host: `<remote-database-host>`
   - Schema: `<database-name>`
   - Login: `<username>`
   - Password: `<password>`
   - Port: `5432`

## 📈 DAG Workflow

The `job_post_dag` executes daily with the following task sequence:

```
┌─────────────────┐
│ is_api_available│
│     @task       │
│    .sensor      │
└────────┬────────┘
         │
         │ API is available
         │
         ▼
┌─────────────────┐
│    extract      │
│     @task       │
└────────┬────────┘
         │
         │ extraction complete
         │
         ▼
┌─────────────────┐
│   transform     │
│     @task       │
└────────┬────────┘
         │
         │ transformation complete
         │
         ▼
┌─────────────────┐
│      load       │
│     @task       │
└─────────────────┘
```

### Task Details

1. **is_api_available**: Sensor that checks API health (60s intervals, 10min timeout)
2. **extract**: Fetches job postings from JSearch API
3. **transform**: Enriches data with skills, benefits, location codes
4. **load**: Inserts data into dimensional data warehouse

### Schedule

- **Frequency**: Daily (`@daily`)
- **Start Date**: January 1, 2026
- **Timezone**: Europe/Paris
- **Catchup**: Disabled
- **Max Consecutive Failures**: 3

## 📊 Connecting to Superset

Once data is loaded into PostgreSQL, connect Apache Superset (remote) to visualize insights:

1. **Add PostgreSQL Database in Superset**
   - Navigate to Data → Databases → + Database
   - Connection String: `postgresql://<user>:<password>@<host>:<port>/<database>`

2. **Create Datasets**
   - Use `fact_job_post` joined with dimension tables
   - Configure metrics and dimensions

3. **Build Dashboards**
   - Job posting trends over time
   - Top technologies in demand
   - Geographic distribution of opportunities
   - Salary ranges by technology
   - Benefits analysis

## 🔍 Data Enrichment Details

### Technologies Detected
- Programming languages (Python, Java, SQL, JavaScript, etc.)
- Data tools (Spark, Kafka, Airflow, dbt, etc.)
- Cloud platforms (AWS, Azure, GCP)
- ML/AI frameworks (TensorFlow, PyTorch, scikit-learn)

### Benefits Identified
- Remote work options
- Health insurance (mutuelle)
- Meal vouchers (tickets restaurant)
- RTT (reduced working time)
- Performance bonuses
- 13th-month salary
- CSE (works council benefits)

## 🧪 Testing and Monitoring

### Run Manual DAG Execution
```bash
# Trigger DAG manually
docker-compose exec airflow-scheduler airflow dags trigger job_post_dag
```

### View Logs
```bash
# Scheduler logs
docker-compose logs -f airflow-scheduler

# Worker logs
docker-compose logs -f airflow-worker
```

### Monitor with Flower (Celery UI)
```bash
docker-compose --profile flower up -d
# Access at http://localhost:5555
```

## 🛡️ Error Handling

- **API Failures**: Sensor retries for 10 minutes before failing
- **Database Errors**: Transactions are rolled back on failure
- **Duplicate Jobs**: Upsert logic prevents duplicates using `job_id`
- **Max Failures**: DAG pauses after 3 consecutive failed runs

## 📝 Development

### Adding New Transformations

Edit [dags/job_post_dag.py](dags/job_post_dag.py) in the `transform` task to add custom logic.

### Extending Data Sources

Add new reference files in the `data/` directory and update transformation logic.

### Custom Airflow Plugins

Place custom operators/sensors in the `plugins/` directory.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

Apache License 2.0

## 👥 Support

For issues, questions, or contributions, please open an issue in the repository.
