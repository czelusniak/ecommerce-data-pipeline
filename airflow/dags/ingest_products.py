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

def ingest_products_logic():
    # ----- 1. Extraction
    print("Fetching data from FakeStore API...")
    url = "https://fakestoreapi.com/products"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    # ----- 2. Transformation
    # Converting the list of dictionaries into a table (DataFrame)
    print(f"2. Transforming {len(data)} products...")
    df = pd.DataFrame(data)

    # Add metadata timestamp
    df['extracted_at'] = datetime.now()

    # Flatten the 'rating' column
    if 'rating' in df.columns:
        df_rating = pd.json_normalize(df['rating'])
        # Drop original rating and join the flattened columns
        df = pd.concat([df.drop(columns=['rating']), df_rating], axis=1)

    # Renaming to use Snake_Case
    df = df.rename(columns={
        "id": "product_id",
        "rate": "rating_value",
        "count": "rating_count"
    })

    df.columns = [
        col.strip().lower().replace(" ", "_").replace(".","_")
        for col in df.columns
    ]

    # ----- 3. Loading (Secure Connection via Airflow Hook)
    print("3. Connecting to Snowflake via Hook...")

    # Airflow retrieves the secure password from its vault
    hook = SnowflakeHook(snowflake_conn_id='snowflake_default')
    engine = hook.get_sqlalchemy_engine()

    print("4. Inserting data into table RAW_DATA.PRODUCTS...")
    with engine.connect() as connection:
        df.to_sql(
            name='products',       # Table's name
            con=engine,
            schema='RAW_DATA',     
            if_exists='replace',   # Full Refresh for now
            index=False,
            method='multi',        # Avoid sending 1 row each time
            chunksize=1000
        )
    print("Success! Load complete.")

with DAG(
    '01_ingest_products',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False,
    tags=['ecommerce', 'ingestion']
) as dag:

    t1 = PythonOperator(
        task_id='ingest_api_products',
        python_callable=ingest_products_logic
    )