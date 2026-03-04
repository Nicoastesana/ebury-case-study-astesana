# Ebury Case Study - ELT Pipeline

## Architecture Overview

This project implements a containerized ELT (Extract, Load, Transform) pipeline using:
- **Apache Airflow**: Orchestration and workflow management
- **dbt (data build tool)**: Data transformation and testing
- **PostgreSQL**: Data warehouse
- **Docker Compose**: Container orchestration

## Project Structure

```
ebury-case-study-astesana/
├── dags/                           # Airflow DAGs
│   └── ebury_elt_pipeline.py      # Main ELT pipeline DAG
├── dbt/                            # dbt project
│   └── ebury_transform/
│       ├── dbt_project.yml        # dbt project configuration
│       ├── profiles.yml           # Database connection profiles
│       └── models/
│           ├── staging/           # Staging models
│           │   ├── sources.yml    # Source definitions
│           │   └── stg_customer_transactions.sql
│           └── analytics/         # Analytics models (star schema)
│               ├── dim_customers.sql      # Customer dimension
│               ├── fact_transactions.sql  # Transaction fact
│               └── schema.yml             # Model tests
├── data/                          # Source data
│   └── customer_transactions.csv  # Sample transaction data
├── init_db/                       # Database initialization scripts
│   └── 01_init.sql               # Creates schemas and permissions
├── logs/                          # Airflow logs (created at runtime)
├── plugins/                       # Airflow plugins (if needed)
├── docker-compose.yml            # Docker services configuration
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## Getting Started

### Prerequisites

- Docker Desktop installed and running
- At least 4GB of RAM available for Docker

### Setup and Run

1. **Start the services**:
   ```powershell
   docker-compose up -d
   ```

2. **Wait for initialization** (first-time setup takes 2-3 minutes):
   ```powershell
   docker-compose logs -f airflow-init
   ```
   Wait until you see "Database migrations complete" and user creation messages.

3. **Access Airflow UI**:
   - URL: http://localhost:8080
   - Username: `airflow`
   - Password: `airflow`

4. **Configure PostgreSQL connection in Airflow**:
   - Go to Admin > Connections
   - Add a new connection:
     - Connection Id: `ebury_dwh`
     - Connection Type: `Postgres`
     - Host: `postgres`
     - Schema: `ebury_dwh`
     - Login: `airflow`
     - Password: `airflow`
     - Port: `5432`

5. **Enable and run the DAG**:
   - In Airflow UI, find `ebury_elt_pipeline`
   - Toggle it to "On"
   - Click "Trigger DAG" to run manually

### Pipeline Flow

1. **Ingest**: Loads `customer_transactions.csv` into `staging.customer_transactions` table
2. **Transform**: dbt runs transformations to create:
   - `staging.stg_customer_transactions` (view)
   - `analytics.dim_customers` (table)
   - `analytics.fact_transactions` (table)
3. **Test**: dbt runs data quality tests (uniqueness, not null, relationships)

### Stopping the Services

```powershell
docker-compose down
```

To remove all data and start fresh:
```powershell
docker-compose down -v
```

## Database Schema

### Staging Layer
- `staging.customer_transactions`: Raw ingested data

### Analytics Layer (Star Schema)
- `analytics.dim_customers`: Customer dimension with aggregated metrics
- `analytics.fact_transactions`: Transaction fact table with foreign key to dim_customers

## Testing

dbt tests include:
- Data integrity checks (unique, not_null)
- Referential integrity (foreign key relationships)
- Custom business logic tests (can be added in `tests/` directory)

## Customization

### Adding New Data Sources
1. Add CSV files to `data/` directory
2. Update DAG in `dags/ebury_elt_pipeline.py` to ingest new sources
3. Define sources in dbt `models/staging/sources.yml`
4. Create staging models in `models/staging/`

### Adding Transformations
1. Create new SQL files in `models/analytics/`
2. Reference upstream models using `{{ ref('model_name') }}`
3. Add tests in corresponding `schema.yml` files

### Scheduling
The DAG is configured to run daily (`schedule_interval='@daily'`). Modify this in `dags/ebury_elt_pipeline.py` as needed.

## Monitoring

- **Airflow UI**: Task status, logs, and execution history
- **PostgreSQL**: Connect directly to inspect tables:
  ```powershell
  docker exec -it ebury_postgres psql -U airflow -d ebury_dwh
  ```

## Troubleshooting

### Services not starting
```powershell
docker-compose logs
```

### Check Airflow scheduler logs
```powershell
docker-compose logs airflow-scheduler
```

### Reset everything
```powershell
docker-compose down -v
docker-compose up -d
```

## Version Management

This project uses **Semantic Versioning** (MAJOR.MINOR.PATCH).

### Current Version
Check the `VERSION` file or see `CHANGELOG.md` for version history.

### Bumping Versions

#### Option 1: Automated Script (Recommended)

```powershell
# For bug fixes (1.0.0 → 1.0.1)
.\scripts\bump-version.ps1 -Type patch -Message "Fix CSV ingestion timeout"

# For new features (1.0.0 → 1.1.0)
.\scripts\bump-version.ps1 -Type minor -Message "Add customer segmentation model"

# For breaking changes (1.0.0 → 2.0.0)
.\scripts\bump-version.ps1 -Type major -Message "Refactor database schema"
```

#### Option 2: Manual Update

1. Edit `VERSION` file with new version number
2. Add entry to `CHANGELOG.md`
3. Commit:
   ```powershell
   git add VERSION CHANGELOG.md
   git commit -m "[release] - Bump version to X.Y.Z"
   ```
4. Create git tag:
   ```powershell
   git tag -a vX.Y.Z -m "Release version X.Y.Z"
   ```

### What the Script Does

The `bump-version.ps1` script automatically:
- ✅ Updates `VERSION` file
- ✅ Updates `CHANGELOG.md` with new entry and date
- ✅ Updates version reference in `docker-compose.yml`
- ✅ Creates git commit with proper message
- ✅ Creates annotated git tag for release tracking

### Publishing a Release

After bumping version:

```powershell
git push
git push --tags
```

## Next Steps

- Add more complex transformations (aggregations, window functions)
- Implement incremental models in dbt
- Add data quality monitoring and alerting
- Implement CI/CD pipeline for automated testing
- Add more comprehensive business metrics and KPIs
