import os
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from google.cloud import bigquery

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

# Your project configuration
PROJECT_ID = "secret-sphinx-470205-r9"
DATASET_ID = "test_dataset_airflow"  # Change this to your dataset name
TABLE_ID = "test_table"
PARQUET_FILE = "/tmp/output.parquet"

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/opt/airflow/secrets/google_credentials.json"

def generate_parquet():
    """Generate sample parquet file"""
    df = pd.DataFrame({
        "name": ["Alice", "Bob", "Charlie"],
        "age": [25, 30, 35],
        "city": ["New York", "Los Angeles", "Chicago"]
    })  
    table = pa.Table.from_pandas(df)
    pq.write_table(table, PARQUET_FILE)
    print(f"✅ Parquet file generated at {PARQUET_FILE}")

def upload_parquet_to_bigquery():
    """Upload parquet file to BigQuery"""
    client = bigquery.Client(project=PROJECT_ID)

    # Create dataset if it doesn't exist
    dataset_id = f"{PROJECT_ID}.{DATASET_ID}"
    try:
        client.get_dataset(dataset_id)
        print(f"✅ Dataset {DATASET_ID} exists")
    except:
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = "US"
        client.create_dataset(dataset, timeout=30)
        print(f"✅ Created dataset {DATASET_ID}")
    
    # Upload DataFrame
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

    # Configure job settings for parquet
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        autodetect=True,
        write_disposition="WRITE_TRUNCATE"
    )

    with open(PARQUET_FILE, 'rb') as source_file:
        job = client.load_table_from_file(source_file,table_id, job_config=job_config)
    
    job.result()  # Wait for the job to complete
    print(f"✅ Uploaded '{PARQUET_FILE}' to {table_id}")

# Airflow DAG definition
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2025, 8, 1),  # Change to your desired start date
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="parquet_to_bq_dag",
    default_args=default_args,
    # schedule_interval=None,
    catchup=False,
    tags=["example"],
) as dag:

    task_generate = PythonOperator(
        task_id="generate_parquet",
        python_callable=generate_parquet,
    )

    task_upload = PythonOperator(
        task_id="upload_to_bigquery",
        python_callable=upload_parquet_to_bigquery,
    )

    task_generate >> task_upload