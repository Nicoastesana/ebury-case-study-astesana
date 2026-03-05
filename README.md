# Ebury Case Study — ELT Pipeline

Containerized ELT platform for Ebury's Senior Data Engineer case study. Orchestrates ingestion of `customer_transactions.csv` into PostgreSQL using Apache Airflow, with dbt handling modular transformations into a star schema, aggregation models, and an auditing layer.

## Architecture

| Layer | Tool | Role |
|---|---|---|
| Orchestration | Apache Airflow | DAG scheduling and task execution |
| Transformation | dbt | Modular SQL models, testing, lineage |
| Warehouse | PostgreSQL | Staging, analytics, auditing schemas |
| Infrastructure | Docker Compose | Containerised, reproducible environment |

## Project Structure

```
ebury-case-study-astesana/
├── dags/
│   └── ebury_elt_pipeline.py        # Main ELT DAG (ingest → dbt run → dbt test)
├── dbt/ebury_transform/
│   ├── dbt_project.yml
│   ├── profiles.yml
│   └── models/
│       ├── staging/
│       │   ├── sources.yml
│       │   └── stg_customer_transactions.sql
│       ├── analytics/               # Star schema
│       │   ├── dim_customers.sql
│       │   ├── fact_transactions.sql
│       │   ├── agg_by_customer.sql
│       │   ├── agg_by_product.sql
│       │   ├── agg_by_customer_product.sql
│       │   └── schema.yml
│       └── auditing/                # Data quality error tracking
│           ├── audit_errors_by_customer.sql
│           └── audit_errors_by_load_date.sql
├── docs/schema/                     # Star schema diagrams
├── init_db/
│   ├── 01_init.sql                  # Creates schemas and permissions
│   └── 02_airflow_db.sql
├── notebooks/
│   └── eda_customer_transactions.ipynb
├── data/                            # Source CSV (gitignored)
├── logs/                            # Airflow logs (gitignored)
├── plugins/                         # Airflow plugins
├── docker-compose.yml
└── requirements.txt
```

## Getting Started

### Prerequisites

- Docker Desktop installed and running
- At least 4GB of RAM available for Docker

### Setup and Run

1. **Create and complete the environment file** (required before starting services):
   ```bash
   cp .env.example .env
   ```
   PowerShell alternative:
   ```powershell
   Copy-Item .env.example .env
   ```
   Then update `.env` with secure values (especially `POSTGRES_PASSWORD`, `_AIRFLOW_WWW_USER_PASSWORD`, and `AIRFLOW__CORE__FERNET_KEY`).

2. **Start all services**:
   ```bash
   docker-compose up -d
   ```
   Note: there is no standalone `dbt` container; `dbt run` and `dbt test` are executed by Airflow tasks inside the Airflow containers.

3. **Wait for initialisation** (~2–3 minutes on first run):
   ```bash
   docker-compose logs -f airflow-init
   ```
   Wait until you see `Database migrations complete`.

4. **Open Airflow UI**: [http://localhost:8080](http://localhost:8080)
   - Username: `airflow` / Password: `airflow`

5. **Configure the PostgreSQL connection** — go to **Admin → Connections** and add:

   | Field | Value |
   |---|---|
   | Connection Id | `ebury_dwh` |
   | Connection Type | `Postgres` |
   | Host | `postgres` |
   | Schema | `ebury_dwh` |
   | Login / Password | `airflow` |
   | Port | `5432` |

6. **Enable and trigger the DAG**: find `ebury_elt_pipeline`, toggle it **On**, then click **Trigger DAG**.

### Stopping the Services

```bash
docker-compose down          # stop containers
docker-compose down -v       # stop and remove all volumes (fresh start)
```

## Pipeline Flow

```
customer_transactions.csv
  → raw.customer_transactions          (Airflow: CSV ingest)
  → staging.stg_customer_transactions  (dbt: cleaned view)
  → analytics.dim_customers            (dbt: customer dimension)
  → analytics.fact_transactions        (dbt: transaction fact table)
  → analytics.agg_by_*                 (dbt: aggregation models)
  → auditing.audit_errors_by_*         (dbt: data quality error tracking)
```

## Database Schema

### Raw Layer
- `raw.customer_transactions` — raw CSV data as ingested

### Staging Layer
- `staging.stg_customer_transactions` — cleaned view with type casting and deduplication

### Analytics Layer (Star Schema)
- `analytics.dim_customers` — customer dimension with aggregated metrics
- `analytics.fact_transactions` — transaction fact table with FK to `dim_customers`
- `analytics.agg_by_customer` — transaction aggregates per customer
- `analytics.agg_by_product` — transaction aggregates per product
- `analytics.agg_by_customer_product` — cross-dimension aggregates

### Auditing Layer
- `auditing.audit_errors_by_customer` — data quality errors grouped by customer
- `auditing.audit_errors_by_load_date` — data quality errors grouped by load date

See [docs/schema/](docs/schema/) for star schema diagrams.

## Data Quality

dbt tests run automatically as the final DAG step and cover:
- Uniqueness and not-null constraints on all key columns
- Referential integrity between fact and dimension tables
- Custom business logic validations

## Monitoring

- **Airflow UI**: task status, logs, and execution history at [http://localhost:8080](http://localhost:8080)
- **PostgreSQL direct access**:
  ```bash
  docker exec -it ebury_postgres psql -U pg_ebury_admin -d ebury_db
  ```

## Troubleshooting

```bash
# View all service logs
docker-compose logs

# Check scheduler specifically
docker-compose logs airflow-scheduler

# Remove orphan containers after compose service changes
docker-compose up -d --remove-orphans

# Full reset
docker-compose down -v && docker-compose up -d
```

## Extending the Pipeline

### Adding a new data source
1. Add the CSV to `data/`
2. Update `dags/ebury_elt_pipeline.py` to ingest it
3. Define it as a source in `dbt/ebury_transform/models/staging/sources.yml`
4. Create a staging model in `models/staging/`

### Adding transformations
1. Create a new SQL file in `models/analytics/` or `models/auditing/`
2. Reference upstream models with `{{ ref('model_name') }}`
3. Add tests to the relevant `schema.yml`

### Changing the schedule
The DAG runs daily by default (`schedule_interval='@daily'`). Edit `dags/ebury_elt_pipeline.py` to change it.
