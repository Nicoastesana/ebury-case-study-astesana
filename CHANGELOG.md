# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-03-04

### Added

- **Initial ELT Pipeline Setup**
  - Docker Compose configuration for containerized deployment
  - PostgreSQL 15 database service with persistent volumes
  - Apache Airflow 2.8.1 (webserver, scheduler, init service)
  - dbt 1.7.7 project for data transformations

- **Airflow Components**
  - Main DAG: `ebury_elt_pipeline` with daily schedule
  - Task 1: CSV ingestion into staging layer
  - Task 2: dbt model execution (staging + analytics)
  - Task 3: Data quality tests via dbt

- **Database Schema**
  - `staging` schema for raw ingested data
  - `analytics` schema for transformed data (star schema)
  - Proper permission grants for airflow user

- **dbt Project Structure**
  - Staging layer: `stg_customer_transactions` (view)
  - Analytics layer:
    - `dim_customers` (dimension table)
    - `fact_transactions` (fact table)
  - Data quality tests: uniqueness, not_null, relationships

- **Sample Data**
  - `customer_transactions.csv` with 5 sample records
  - Ready-to-run pipeline for demonstration

- **Configuration Files**
  - `requirements.txt` with all Python dependencies
  - Database initialization script (`init_db/01_init.sql`)
  - dbt profiles and project configuration
  - Comprehensive README with setup instructions

- **Project Structure**
  - `.gitignore` with proper exclusions
  - `VERSION` file for semantic versioning
  - Placeholder directories for logs and plugins

### Services Included

| Service | Version | Port |
|---------|---------|------|
| PostgreSQL | 15 | 5432 |
| Airflow | 2.8.1 | 8080 |
| dbt-core | 1.7.7 | - |
| dbt-postgres | 1.7.7 | - |

### Getting Started

```bash
docker-compose up -d
```

Access Airflow UI at `http://localhost:8080` with credentials `airflow:airflow`

---

## Version Format

This project uses **Semantic Versioning**: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes (schema changes, service upgrades)
- **MINOR**: New features (new models, new data sources)
- **PATCH**: Bug fixes and improvements

### How to Update Version

1. Edit the `VERSION` file
2. Update this `CHANGELOG.md`
3. Commit with message: `[release] - Bump version to X.Y.Z`
4. Create git tag: `git tag -a vX.Y.Z -m "Release version X.Y.Z"`

