# dbt-snowflake-airflow

Data engineering project using Apache Airflow, Snowflake, and dbt.

This project was initially based on the YouTube tutorial [here](https://www.youtube.com/watch?v=mBrk5hvqc84) by [@wlcamargo](https://github.com/wlcamargo) (in Portuguese) and the file organization was modified following dbt best practices for splitting SQL into staging, intermediate and marts layers as discussed in [this dbt Community Forum thread](https://discourse.getdbt.com/t/best-practice-splitting-sql-into-staging-intermediate-and-marts-layers-and-naming-conventions/11372).

## Architecture

![Architecture](assets/architecture-dbt-snowflake-airflow.png)

## Step by step contained in this repo

1. Create a Snowflake account
2. Install Docker
3. Connect dbt to Snowflake
4. Ingest CSV file to Snowflake with dbt
5. Create the dbt image in a container
6. Orchestrate the dbt container connected to Snowflake with Airflow

## Requirements

- Docker and Docker Compose
- Python >= 3
- Snowflake account (https://signup.snowflake.com/)

## Installation

**1. Run the WSL in your PowerShell**

**2. Clone the repository in the Ubuntu folder:**
```bash
git clone https://github.com/czelusniak/ecommerce-data-pipeline.git
cd dbt-snowflake-airflow
```

**3. Install Docker:**
   - Follow the official Docker installation guide for your operating system:
     - [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
     - [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
     - [Docker Engine for Linux](https://docs.docker.com/engine/install/)
   - Verify the installation:
     ```bash
     docker --version
     docker compose version
     ```

**4. Run Snowflake setup SQL commands:**
   - Open a Snowflake worksheet and execute the SQL commands from `scripts/snowflake-setup.sql` in your Snowflake account
   - This will create the necessary warehouse, database, schema, role, and user for dbt

**5. On WSL, create and activate a virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**6. Install requirements:**
```bash
pip install -r requirements.txt
```
> **Note:** Make sure your virtual environment is activated for the following steps.


**7. Verify dbt installation:**
```bash
dbt --version
```

**8. Start and access Airflow:**
```bash
cd airflow
docker compose up -d
```

Expected result:

<img width="348" height="178" alt="image" src="https://github.com/user-attachments/assets/7b630669-fb42-43e7-81cc-61b54e34ef53" />

- Access the Airflow using the URL: http://localhost:8081
- Username: `airflow`
- Password: `airflow`


**9. Configure Snowflake connection:**
   - Rename `src/dbt/example-profiles.yml` to `profiles.yml`
   - Edit `src/dbt/profiles.yml` and replace `your-account-here` with your Snowflake account name


**10. Test dbt connection with Snowflake:**
```bash
cd src/dbt && dbt debug
```
Expected result:

![Connection OK](assets/connection-dbt-snow-ok.png)


**11. Ingest data (local test, before using Docker):**
```bash
cd src/dbt && dbt seed
```
This will load the CSV files from the `seeds/` directory into Snowflake.

Expected result:

![dbt seed success](assets/dbt-seed.png)

> **Note:** This is a local test. Later, we will use the Docker container for ingestion instead of running locally.

**12. Create Docker image for dbt:**
   - Create the dbt Docker image:
   ```bash
   cd src
   docker build -t dbt-snowflake .
   ```
   - Enter the dbt container (optional, for debugging):
   ```bash
   docker run -it dbt-snowflake /bin/bash
   ```
   > **Note:** This Docker image will be used by Airflow to run dbt transformations.


**13. Test the container:**
   - Modify the data in the `seeds/` directory
   - Run the seed command again:
   ```bash
   cd src/dbt && dbt seed
   ```
   - Verify the updates in your Snowflake account


**14. View orchestration in Airflow:**

You can see the DAG (Directed Acyclic Graph) in the Airflow UI:

![Airflow DAG](assets/dag-sample.png)


## Stopping the Project

To stop the project and free up system resources, run:

```bash
cd airflow
docker compose down
```

## Project Structure

The project follows dbt best practices with a layered architecture:

```
src/dbt/
├── models/
│   ├── 1staging/      # Staging models - initial data cleaning and standardization
│   ├── 2intermediate/ # Intermediate models - business logic transformations
│   └── 3marts/        # Mart models - final analytics-ready tables
├── seeds/             # CSV files to be loaded into Snowflake
├── macros/            # Reusable SQL macros
└── profiles.yml       # Snowflake connection configuration
```

## References

- [Base repo](https://github.com/jacob-mennell/snowflakeAirflowDBT)
- [Base repo 2](https://github.com/wlcamargo/dbt-snowflake-airflow)
- [Snowflake Guide](https://quickstarts.snowflake.com/guide/data_engineering_with_apache_airflow/index.html)
