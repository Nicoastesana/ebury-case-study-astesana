# ebury-case-study-astesana
Containerized ELT platform for Ebury's Senior Data Engineer case study. Uses Airflow to orchestrate the ingestion of customer_transactions.csv into PostgreSQL, with dbt handling modular transformations into a star schema (dim/fact). Focused on platform scalability, Docker-native deployment, and rigorous data quality via dbt-test.
