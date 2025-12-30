from datetime import datetime
from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator

default_args = {
    "owner": "George Czelusniak",
    "depends_on_past": False,
}

with DAG(
    dag_id="dbt-snowflake-process",
    default_args=default_args,
    start_date=datetime(2024, 10, 31),
    schedule_interval="@hourly",
    catchup=False,
    tags=["dbt", "snowflake"],
) as dag:

    # Task 1: Load seed data (CSV files) into Snowflake
    run_seeds = DockerOperator(
        task_id="run_seeds",
        image="dbt-snowflake",
        container_name="dbt_seeds",
        api_version="auto",
        auto_remove=True,
        command="dbt seed --profiles-dir .",
        docker_url="tcp://docker-proxy:2375",
        network_mode="airflow_default",
        mount_tmp_dir=False,
    )

    # Task 2: Run staging models (basic transformations of seeds)
    run_staging = DockerOperator(
        task_id="run_staging",
        image="dbt-snowflake",
        container_name="dbt_staging",
        api_version="auto",
        auto_remove=True,
        command="dbt run --select 1staging --profiles-dir .",
        docker_url="tcp://docker-proxy:2375",
        network_mode="airflow_default",
        mount_tmp_dir=False,
    )

    # Task 3: Run intermediate and mart models (dbt automatically resolves dependencies)
    run_intermediate_and_marts = DockerOperator(
        task_id="run_intermediate_and_marts",
        image="dbt-snowflake",
        container_name="dbt_marts",
        api_version="auto",
        auto_remove=True,
        command="dbt run --select 2intermediate 3marts --profiles-dir .",
        docker_url="tcp://docker-proxy:2375",
        network_mode="airflow_default",
        mount_tmp_dir=False,
    )

    # Define execution order: seeds -> staging -> intermediate/marts
    run_seeds >> run_staging >> run_intermediate_and_marts
