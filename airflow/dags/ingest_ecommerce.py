from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
from datetime import datetime
import requests
import pandas as pd

default_args = {
    'owner': 'George Czelusniak',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'retries': 0,
}

def ingest_data(endpoint, table_name):
    # ----- 1. EXTRACTION
    print("Fetching data from FakeStore API...")
    url = f"https://fakestoreapi.com/{endpoint}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()


    # ----- 2. TRANSFORMATION
    # Converting the list of dictionaries into a table (DataFrame)
    print(f"2. Transforming {len(data)} rows for {table_name}...")
    df = pd.DataFrame(data)

    # Add metadata timestamp
    df['extracted_at'] = datetime.now()

    df.columns = [
        col.strip().lower().replace(" ", "_").replace(".","_")
        for col in df.columns
    ]

    # Carts have lists inside columns (e.g., [{'productId':1...}]).
    # Pandas to_sql hates lists. We must convert them to strings first.
    for col in df.columns:
        # Check if the column contain lists or dicts
        if df[col].apply(lambda x: isinstance(x, (list, dict))).any():
            print(f"   -> Flattening complex column: {col}")
            df[col] = df[col].astype(str)


    # ----- 3. LOADING (Secure Connection via Airflow Hook)
    print(f"3. Connecting to Snowflake to write to RAW_DATA.{table_name}...")

    # Airflow retrieves the secure password from its vault
    hook = SnowflakeHook(snowflake_conn_id='snowflake_default')
    engine = hook.get_sqlalchemy_engine()

    print(f"4. Inserting data into table RAW_DATA.{table_name}...")
    with engine.connect() as connection:
        df.to_sql(
            name=table_name.lower(),       # Table's name
            con=engine,
            schema='RAW_DATA',     
            if_exists='replace',   # Full Refresh for now
            index=False,
            method='multi',        # Avoid sending 1 row each time
            chunksize=1000
        )
    print("Success! Load complete.")

with DAG(
    '01_ingest_ecommerce',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False,
    tags=['ecommerce', 'ingestion']
) as dag:

    # Task 1: Ingest Products
    t_products = PythonOperator(
        task_id='ingest_products',
        python_callable=ingest_data,  # Call the generic function
        op_kwargs={
            'endpoint': 'products', 
            'table_name': 'PRODUCTS' # Passing Uppercase directly is safer
        }
    )

    # Task 2: Ingest Carts 
    t_carts = PythonOperator(
        task_id='ingest_carts',
        python_callable=ingest_data,
        op_kwargs={
            'endpoint': 'carts', 
            'table_name': 'CARTS'
        }
    )