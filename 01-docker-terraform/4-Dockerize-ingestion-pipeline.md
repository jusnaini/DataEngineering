# Dockerize Ingestion Pipeline

This note describes how to dockerize an ingestion pipeline for the NY Taxi dataset.
Once built, the pipeline can be easily deployed using Docker to load data into a pre-created database (ny_taxi).

## 1. Create the ingestion pipeline script
Start with a simple [test script](pipeline.py) to understand how CLI arguments are parsed:

```python
import sys
import argparse

import pandas as pd

print("Starting the data processing pipeline...")
print (sys.argv)

date = sys.argv[1]
print (f'Date provided: {date}')
```

Then save the following as **```ingest_data.py```**:
```python
#!/usr/bin/env python
# coding: utf-8

import os
import argparse
from time import time

import pandas as pd
from sqlalchemy import create_engine


def main(params):
    user = params.user
    password = params.password
    host = params.host
    port = params.port
    db = params.db
    table_name = params.table_name
    url = params.url

    # the backup files are gzipped, keep the correct extension
    # for pandas to read it properly
    if url.endswith('.csv.gz'):
        csv_name = 'output.csv.gz'
    else:
        csv_name = 'output.csv'

    os.system(f"wget {url} -O {csv_name}")

    engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{db}')

    df_iter = pd.read_csv(csv_name, iterator=True, chunksize=100000)

    df = next(df_iter)

    df.tpep_pickup_datetime = pd.to_datetime(df.tpep_pickup_datetime)
    df.tpep_dropoff_datetime = pd.to_datetime(df.tpep_dropoff_datetime)

    df.head(n=0).to_sql(name=table_name, con=engine, if_exists='replace')
    df.to_sql(name=table_name, con=engine, if_exists='append')

    while True:
        try:
            t_start = time()
            df = next(df_iter)

            df.tpep_pickup_datetime = pd.to_datetime(df.tpep_pickup_datetime)
            df.tpep_dropoff_datetime = pd.to_datetime(df.tpep_dropoff_datetime)

            df.to_sql(name=table_name, con=engine, if_exists='append')

            t_end = time()
            print(f"Inserted another chunk, took {t_end - t_start:.3f} second")

        except StopIteration:
            print("Finished ingesting data into the Postgres database")
            break


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Ingest CSV data to Postgres')

    parser.add_argument('--user', required=True, help='username for postgres')
    parser.add_argument('--password', required=True, help='password for postgres')
    parser.add_argument('--host', required=True, help='host for postgres')
    parser.add_argument('--port', required=True, help='port for postgres')
    parser.add_argument('--db', required=True, help='database name for postgres')
    parser.add_argument('--table_name', required=True, help='table name for writing results')
    parser.add_argument('--url', required=True, help='URL of the CSV file')

    args = parser.parse_args()
    main(args)
```

## 2. Run the Postgres database container

Create a Docker network for communication between containers:
```bash
docker network create pg-network
```

Run Postgres:
```bash
docker run -it \
  -e POSTGRES_USER="root" \
  -e POSTGRES_PASSWORD="root" \
  -e POSTGRES_DB="ny_taxi" \
  -v ny_taxi_pg_data:/var/lib/postgresql/data \
  -p 5432:5432 \
  --network=pg-network \
  --name pg-database \
  postgres:13
```

## 3. Run pgAdmin for easier database interaction
```bash
docker run -it -p 80:80 \
  -e PGADMIN_DEFAULT_EMAIL="admin@admin.com" \
  -e PGADMIN_DEFAULT_PASSWORD="root" \
  --network=pg-network \
  --name pgadmin-client \
  -d dpage/pgadmin4
```

Both **pg-database** and **pgadmin-client** must be attached to the same network (**pg-network**).


## Re-using existing containers

⚠️ `docker run` always creates a new container. To re-use an existing one, use `docker start`:

```bash
docker start pg-database
docker start pgadmin-client
```

`docker stop ` to stop the running container:
```bash
docker stop pg-database
docker stop pgadmin-client

```
## 4. Test the ingestion script locally

Before dockerizing the pipeline, test it from the local machine:

```bash
URL="https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/yellow_tripdata_2021-01.csv.gz"

python ingest_data.py \
  --user=root \
  --password=root \
  --host=localhost \
  --port=5432 \
  --db=ny_taxi \
  --table_name=yellow_taxi_trips \
  --url=${URL}
```

## 5. Verify the table creation

A new **table** `yellow_taxi_trips` should now exist in the `ny_taxi` **database**.

Verification options:
1. In **pgAdmin** (localhost:80), refresh the ny_taxi database → Schemas → Tables → confirm the table exists.
2. Using **pgcli** (if installed):
```bash
pgcli -h localhost -p 5432 -U root -d ny_taxi
```

Then inside pgcli:

```bash
\dt
```

## 6. Dockerize the ingestion script

Create a Dockerfile:

```bash
FROM python:3.13.5

RUN apt-get update && apt-get install -y wget
RUN pip install pandas sqlalchemy psycopg2

WORKDIR /app
COPY ingest_data.py ingest_data.py 

ENTRYPOINT [ "python", "ingest_data.py" ]
```


Build the image:

```bash
docker build -t taxi_ingest:v001 .
```

## 7. Run the ingestion container

First, check that the image is built:

```bash
docker images
```


Then run the ingestion container:

```bash
URL="https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/yellow_tripdata_2021-01.csv.gz"

docker run -it \
  --network=pg-network \
  taxi_ingest:v001 \
    --user=root \
    --password=root \
    --host=pg-database \
    --port=5432 \
    --db=ny_taxi \
    --table_name=yellow_taxi_trips \
    --url=${URL}

```

✅ At this point, the ingestion pipeline is dockerized and can load data directly into the Postgres container.

Protip:

```bash
URL="https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/yellow_tripdata_2021-01.csv.gz"

docker run -it --rm \
  --network=pg-network \
  taxi_ingest:v001 \
    --user=root \
    --password=root \
    --host=pg-database \
    --port=5432 \
    --db=ny_taxi \
    --table_name=yellow_taxi_trips \
    --url=${URL}
```

🔑 What --rm does:

Once the ingestion script finishes and the container exits, Docker will remove it automatically.

This is great for one-off jobs (like ingestion, ETL tasks, testing).

Saves you from cluttering your system with stopped containers (docker ps -a).

👉 For long-running services (like postgres, pgAdmin, or web apps), don’t use --rm, because you usually want those containers to restart if stopped, and keep their state.
