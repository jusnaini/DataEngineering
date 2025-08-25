# Ingesting NY Taxi Data to Postgres

This guide explains how to set up a Postgres database in Docker and ingest the NY Taxi dataset.

---

## 1. Run Postgres in Docker

Pull a specific version of Postgres (avoid `latest`):

```bash
docker pull postgres:13
```
or 

```bash
docker pull postgres:14.5
```

⚠️ Why not `latest`

    The :latest tag changes with each release. New versions may introduce breaking changes or vulnerabilities, so it’s safer to lock to a known version.


Start Postgres:

```bash
docker run -it \
    -e POSTGRES_USER="root" \
    -e POSTGRES_PASSWORD="root" \
    -e POSTGRES_DB="ny_taxi" \
    -v postgres-db-volume:/var/lib/postgresql/data \
    -p 5432:5432 \
    -d postgres:13
```


📝 **Notes**:

* `-it` → interactive terminal (not needed with `-d`, but fine if you test interactively).
* `-e` → environment variables (`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`).
* `-v` → mount a Docker named volume (`postgres-db-volume`) to persist DB files.
* `-p 5432:5432` → map container’s Postgres port to local machine.
* `-d` → run in detached (background) mode.
* `postgres:13` → image to run.

👉 If the image is not already downloaded, Docker will pull it automatically.

👉 Check running containers with:

```bash
docker ps
```
---
### Named volumes vs host directory mapping

You can persist Postgres data either with a **named volume** (managed by Docker) or a **bind mount** (map to a host folder).

#### Bind mount (local folder):

```bash
docker run -it \
    -e POSTGRES_USER="root" \
    -e POSTGRES_PASSWORD="root" \
    -e POSTGRES_DB="ny_taxi" \
    -v $(pwd)/ny_taxi_pg_data:/var/lib/postgresql/data \
    -p 5432:5432 \
    -d postgres:13
```

- This maps ./ny_taxi_pg_data on your host machine → /var/lib/postgresql/data inside the container.

- Docker `will NOT` list it in `docker volume ls` since it’s just a directory mapping.

#### Named volume (managed by Docker):

```bash
docker run -it \
    -e POSTGRES_USER="root" \
    -e POSTGRES_PASSWORD="root" \
    -e POSTGRES_DB="ny_taxi" \
    -v ny_taxi_pg_data:/var/lib/postgresql/data \
    -p 5432:5432 \
    -d postgres:13

```

- Creates a Docker-managed volume (ny_taxi_pg_data).

- `Will show` up in `docker volume ls`.

Summary:

```bash
./ny_taxi_pg_data:/var/lib/postgresql/data   # host directory (bind mount)
ny_taxi_pg_data:/var/lib/postgresql/data     # Docker named volume
```

## 2. Verify the Database
**Using** `pgcli`

Install:

```bash
pip install pgcli
```


Connect:

```bash
pgcli -h localhost -p 5432 -U root -d ny_taxi
```


Inside pgcli:

```bash
\dt   # list tables
```

## 3. Ingest Data

📂 Data source: [NYC Taxi Trip Records](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)

To test ingestion using [jupyter notebook:](test_connect_ingest.ipynb)
```python
from sqlalchemy import create_engine
import pandas as pd
from time import time

engine = create_engine('postgresql://root:root@localhost:5432/ny_taxi')

# Prepare schema (DDL)
print(pd.io.sql.get_schema(df, name='yellow_tripdata_2021_01', con=engine))

# Read CSV in chunks
df_iter = pd.read_csv(
    'yellow_tripdata_2021-01.csv',
    iterator=True,
    chunksize=100000,
    parse_dates=["tpep_pickup_datetime", "tpep_dropoff_datetime"]
)

# Create empty table with headers
df = next(df_iter)
df.head(0).to_sql(name='yellow_tripdata_2021_01', con=engine, if_exists='replace', index=False)

# Insert chunks
count = 0
while True:
    t_start = time()
    try:
        chunk = next(df_iter)
        chunk.to_sql(name='yellow_tripdata_2021_01', con=engine, if_exists='append', index=False)
        count += 1
        print(f'Inserted batch {count} in {time() - t_start:.2f} seconds')
    except StopIteration:
        print("Ingestion complete.")
        break

```
✅ At this point, the NY Taxi data is ingested into the Postgres database.

👉 For a more automated approach, see:[Dockerize Ingestion Pipeline](4-Dockerize-ingestion-pipeline.md)


