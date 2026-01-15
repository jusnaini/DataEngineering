# 01 - Introduction to Docker

**[↑ Up](README.md)** | **[← Previous](README.md)** | **[Next →](02-virtual-environment.md)**

Docker is a _containerization software_ that allows us to isolate software in a similar way to virtual machines but in a much leaner way.

A Docker image is a _snapshot_ of a container that we can define to run our software, or in this case our data pipelines. By exporting our Docker images to Cloud providers such as Amazon Web Services or Google Cloud Platform we can run our containers there.

## Why Docker?

Docker provides the following advantages:

- Reproducibility: Same environment everywhere
- Isolation: Applications run independently
- Portability: Run anywhere Docker is installed

They are used in many situations:

- Integration tests: CI/CD pipelines
- Running pipelines on the cloud: AWS Batch, Kubernetes jobs
- Spark: Analytics engine for large-scale data processing
- Serverless: AWS Lambda, Google Functions

## Basic Docker Commands

Check Docker version:

```bash
docker --version
```

Run a simple container:

```bash
docker run hello-world
```

Run something more complex:

```bash
docker run ubuntu
```

Nothing happens. Need to run it in `-it` mode:

```bash
docker run -it ubuntu
```

We don't have `python` there so let's install it:

```bash
apt update && apt install python3
python3 -V
```

## Stateless Containers

Important: Docker containers are stateless - any changes done inside a container will NOT be saved when the container is killed and started again.

When you exit the container and use it again, the changes are gone:

```bash
docker run -it ubuntu
python3 -V
```

This is good, because it doesn't affect your host system. Let's say you do something crazy like this:

```bash
docker run -it ubuntu
rm -rf / # don't run it on your computer!
```

Next time we run it, all the files are back.

## Managing Containers

But, this is not _completely_ correct. The state is saved somewhere. We can see stopped containers:

```bash
docker ps -a
```

We can restart one of them, but we won't do it, because it's not a good practice. They take space, so let's delete them:

```bash
docker rm `docker ps -aq`
```

Next time we run something, we add `--rm`:

```bash
docker run -it --rm ubuntu
```

## Different Base Images

There are other base images besides `hello-world` and `ubuntu`. For example, Python:

```bash
docker run -it --rm python:3.9.16
# add -slim to get a smaller version
```

This one starts `python`. If we want bash, we need to overwrite `entrypoint`:

```bash
docker run -it \
    --rm \
    --entrypoint=bash \
    python:3.9.16-slim
```

## Volumes

So, we know that with docker we can restore any container to its initial state in a reproducible manner. But what about data? A common way to do so is with _volumes_.

Let's create some data in `test`:

```bash
mkdir test
cd test
touch file1.txt file2.txt file3.txt
echo "Hello from host" > file1.txt
cd ..
```

Now let's create a simple script `test/list_files.py` that shows the files in the folder:

```python
from pathlib import Path

current_dir = Path.cwd()
current_file = Path(__file__).name

print(f"Files in {current_dir}:")

for filepath in current_dir.iterdir():
    if filepath.name == current_file:
        continue

    print(f"  - {filepath.name}")

    if filepath.is_file():
        content = filepath.read_text(encoding='utf-8')
        print(f"    Content: {content}")
```

Now let's map this to a Python container:

```bash
docker run -it \
    --rm \
    -v $(pwd)/test:/app/test \
    --entrypoint=bash \
    python:3.9.16-slim
```

Inside the container, run:

```bash
cd /app/test
ls -la
cat file1.txt
python list_files.py
```

You'll see the files from your host machine are accessible in the container!

---

# 02 - Virtual Environments and Data Pipelines

A **data pipeline** is a service that receives data as input and outputs more data. For example, reading a CSV file, transforming the data somehow and storing it as a table in a PostgreSQL database.

```mermaid
graph LR
    A[CSV File] --> B[Data Pipeline]
    B --> C[Parquet File]
    B --> D[PostgreSQL Database]
    B --> E[Data Warehouse]
    style B fill:#4CAF50,stroke:#333,stroke-width:2px,color:#fff
```

In this workshop, we'll build pipelines that:

- Download CSV data from the web
- Transform and clean the data with pandas
- Load it into PostgreSQL for querying
- Process data in chunks to handle large files

## Creating a Simple Pipeline

Let's create an example pipeline. First, create a directory `pipeline` and inside, create a file  `pipeline.py`:

```python
import sys
print("arguments", sys.argv)

day = int(sys.argv[1])
print(f"Running pipeline for day {day}")
```

Now let's add pandas:

```python
import pandas as pd

df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
print(df.head())

df.to_parquet(f"output_day_{sys.argv[1]}.parquet")
```

## Why Virtual Environments?

We need pandas, but we don't have it. We want to test it before we run things in a container.

We can install it with `pip`:

```bash
pip install pandas pyarrow
```

But this installs it globally on your system. This can cause conflicts if different projects need different versions of the same package.

Instead, we want to use a **virtual environment** - an isolated Python environment that keeps dependencies for this project separate from other projects and from your system Python.

## Using uv - Modern Python Package Manager

We'll use `uv` - a modern, fast Python package and project manager written in Rust. It's much faster than pip and handles virtual environments automatically.

```bash
pip install uv
```

Now initialize a Python project with uv:

```bash
uv init --python=3.13
```

This creates a `pyproject.toml` file for managing dependencies and a `.python-version` file.

### Comparing Python Versions

```bash
uv run which python  # Python in the virtual environment
uv run python -V

which python        # System Python
python -V
```

You'll see they're different - `uv run` uses the isolated environment.

### Adding Dependencies

Now let's add pandas:

```bash
uv add pandas pyarrow
```

This adds pandas to your `pyproject.toml` and installs it in the virtual environment.

### Running the Pipeline

Now we can execute the file:

```bash
uv run python pipeline.py 10
```

We will see:

* `['pipeline.py', '10']`
* `job finished successfully for day = 10`

## Git Configuration

This script produces a binary (parquet) file, so let's make sure we don't accidentally commit it to git by adding parquet extensions to `.gitignore`:

```
*.parquet
```

---



# 03 - Dockerizing the Pipeline


Now let's containerize the script. Create the following `Dockerfile` file:

## Simple Dockerfile with pip

```dockerfile
# base Docker image that we will build on
FROM python:3.13.11-slim

# set up our image by installing prerequisites; pandas in this case
RUN pip install pandas pyarrow

# set up the working directory inside the container
WORKDIR /app
# copy the script to the container. 1st name is source file, 2nd is destination
COPY pipeline.py pipeline.py

# define what to do first when the container runs
# in this example, we will just run the script
ENTRYPOINT ["python", "pipeline.py"]
```

**Explanation:**

- `FROM`: Base image (Python 3.13)
- `RUN`: Execute commands during build
- `WORKDIR`: Set working directory
- `COPY`: Copy files into the image
- `ENTRYPOINT`: Default command to run

### Build and Run

Let's build the image:

```bash
docker build -t test:pandas .
```

* The image name will be `test` and its tag will be `pandas`. If the tag isn't specified it will default to `latest`.

We can now run the container and pass an argument to it, so that our pipeline will receive it:

```bash
docker run -it test:pandas some_number
```

You should get the same output you did when you ran the pipeline script by itself.

> Note: these instructions assume that `pipeline.py` and `Dockerfile` are in the same directory. The Docker commands should also be run from the same directory as these files.

## Dockerfile with uv

What about uv? Let's use it instead of using pip:

```dockerfile
# Start with slim Python 3.13 image
FROM python:3.13.10-slim

# Copy uv binary from official uv image (multi-stage build pattern)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

# Set working directory
WORKDIR /app

# Add virtual environment to PATH so we can use installed packages
ENV PATH="/app/.venv/bin:$PATH"

# Copy dependency files first (better layer caching)
COPY "pyproject.toml" "uv.lock" ".python-version" ./
# Install dependencies from lock file (ensures reproducible builds)
RUN uv sync --locked

# Copy application code
COPY pipeline.py pipeline.py

# Set entry point
ENTRYPOINT ["python", "pipeline.py"]
```

---



# 04 - Running PostgreSQL with Docker

Now we want to do real data engineering. Let's use a Postgres database for that.

You can run a containerized version of Postgres that doesn't require any installation steps. You only need to provide a few _environment variables_ to it as well as a _volume_ for storing data.

## Running PostgreSQL in a Container

Create a folder anywhere you'd like for Postgres to store data in. We will use the example folder `ny_taxi_postgres_data`. Here's how to run the container:

```bash
docker run -it --rm \
  -e POSTGRES_USER="root" \
  -e POSTGRES_PASSWORD="root" \
  -e POSTGRES_DB="ny_taxi" \
  -v ny_taxi_postgres_data:/var/lib/postgresql \
  -p 5432:5432 \
  postgres:18
```

### Explanation of Parameters

* `-e` sets environment variables (user, password, database name)
* `-v ny_taxi_postgres_data:/var/lib/postgresql` creates a **named volume**
  * Docker manages this volume automatically
  * Data persists even after container is removed
  * Volume is stored in Docker's internal storage
* `-p 5432:5432` maps port 5432 from container to host
* `postgres:18` uses PostgreSQL version 18 (latest as of Dec 2025)

### Alternative Approach - Bind Mount

First create the directory, then map it:

```bash
mkdir ny_taxi_postgres_data

docker run -it \
  -e POSTGRES_USER="root" \
  -e POSTGRES_PASSWORD="root" \
  -e POSTGRES_DB="ny_taxi" \
  -v $(pwd)/ny_taxi_postgres_data:/var/lib/postgresql \
  -p 5432:5432 \
  postgres:18
```

### Named Volume vs Bind Mount

* **Named volume** (`name:/path`): Managed by Docker, easier
* **Bind mount** (`/host/path:/container/path`): Direct mapping to host filesystem, more control

## Connecting to PostgreSQL

Once the container is running, we can log into our database with [pgcli](https://www.pgcli.com/).

Install pgcli:

```bash
uv add --dev pgcli
```

The `--dev` flag marks this as a development dependency (not needed in production). It will be added to the `[dependency-groups]` section of `pyproject.toml` instead of the main `dependencies` section.

Now use it to connect to Postgres:

```bash
uv run pgcli -h localhost -p 5432 -u root -d ny_taxi
```

* `uv run` executes a command in the context of the virtual environment
* `-h` is the host. Since we're running locally we can use `localhost`.
* `-p` is the port.
* `-u` is the username.
* `-d` is the database name.
* The password is not provided; it will be requested after running the command.

When prompted, enter the password: `root`

## Basic SQL Commands

Try some SQL commands:

```sql
-- List tables
\dt

-- Create a test table
CREATE TABLE test (id INTEGER, name VARCHAR(50));

-- Insert data
INSERT INTO test VALUES (1, 'Hello Docker');

-- Query data
SELECT * FROM test;

-- Exit
\q
```

---



# 05 - NY Taxi Dataset and Data Ingestion

We will now create a Jupyter Notebook `notebook.ipynb` file which we will use to read a CSV file and export it to Postgres.

## Setting up Jupyter

Install Jupyter:

```bash
uv add --dev jupyter
```

Let's create a Jupyter notebook to explore the data:

```bash
uv run jupyter notebook
```

## The NYC Taxi Dataset

We will use data from the [NYC TLC Trip Record Data website](https://www1.nyc.gov/site/tlc/about/tlc-trip-record-data.page).

Specifically, we will use the [Yellow taxi trip records CSV file for January 2021](https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/yellow_tripdata_2021-01.csv.gz).

This data used to be csv, but later they switched to parquet. We want to keep using CSV because we need to do a bit of extra pre-processing (for the purposes of learning it).

A dictionary to understand each field is available [here](https://www1.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf).

> Note: The CSV data is stored as gzipped files. Pandas can read them directly.

## Explore the Data

Create a new notebook and run:

```python
import pandas as pd

# Read a sample of the data
prefix = 'https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/'
df = pd.read_csv(prefix + 'yellow_tripdata_2021-01.csv.gz', nrows=100)

# Display first rows
df.head()

# Check data types
df.dtypes

# Check data shape
df.shape
```

### Handling Data Types

We have a warning:

```
/tmp/ipykernel_25483/2933316018.py:1: DtypeWarning: Columns (6) have mixed types. Specify dtype option on import or set low_memory=False.
```

So we need to specify the types:

```python
dtype = {
    "VendorID": "Int64",
    "passenger_count": "Int64",
    "trip_distance": "float64",
    "RatecodeID": "Int64",
    "store_and_fwd_flag": "string",
    "PULocationID": "Int64",
    "DOLocationID": "Int64",
    "payment_type": "Int64",
    "fare_amount": "float64",
    "extra": "float64",
    "mta_tax": "float64",
    "tip_amount": "float64",
    "tolls_amount": "float64",
    "improvement_surcharge": "float64",
    "total_amount": "float64",
    "congestion_surcharge": "float64"
}

parse_dates = [
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime"
]

df = pd.read_csv(
    prefix + 'yellow_tripdata_2021-01.csv.gz',
    nrows=100,
    dtype=dtype,
    parse_dates=parse_dates
)
```

## Ingesting Data into Postgres

In the Jupyter notebook, we create code to:

1. Download the CSV file
2. Read it in chunks with pandas
3. Convert datetime columns
4. Insert data into PostgreSQL using SQLAlchemy

### Install SQLAlchemy

```bash
uv add sqlalchemy psycopg2-binary
```

### Create Database Connection

```python
from sqlalchemy import create_engine
engine = create_engine('postgresql://root:root@localhost:5432/ny_taxi')
```

### Get DDL Schema

```python
print(pd.io.sql.get_schema(df, name='yellow_taxi_data', con=engine))
```

Output:

```sql
CREATE TABLE yellow_taxi_data (
    "VendorID" BIGINT,
    tpep_pickup_datetime TIMESTAMP WITHOUT TIME ZONE,
    tpep_dropoff_datetime TIMESTAMP WITHOUT TIME ZONE,
    passenger_count BIGINT,
    trip_distance FLOAT(53),
    "RatecodeID" BIGINT,
    store_and_fwd_flag TEXT,
    "PULocationID" BIGINT,
    "DOLocationID" BIGINT,
    payment_type BIGINT,
    fare_amount FLOAT(53),
    extra FLOAT(53),
    mta_tax FLOAT(53),
    tip_amount FLOAT(53),
    tolls_amount FLOAT(53),
    improvement_surcharge FLOAT(53),
    total_amount FLOAT(53),
    congestion_surcharge FLOAT(53)
)
```

### Create the Table

```python
df.head(n=0).to_sql(name='yellow_taxi_data', con=engine, if_exists='replace')
```

`head(n=0)` makes sure we only create the table, we don't add any data yet.

## Ingesting Data in Chunks

We don't want to insert all the data at once. Let's do it in batches and use an iterator for that:

```python
df_iter = pd.read_csv(
    ...
    iterator=True,
    chunksize=100000
)
```

### Iterate Over Chunks

```python
for df_chunk in df_iter:
    print(len(df_chunk))
```

### Inserting Data

```python
df_chunk.to_sql(name='yellow_taxi_data', con=engine, if_exists='append')
```

### Complete Ingestion Loop

```python
first = True

for df_chunk in df_iter:

    if first:
        # Create table schema (no data)
        df_chunk.head(0).to_sql(
            name="yellow_taxi_data",
            con=engine,
            if_exists="replace"
        )
        first = False
        print("Table created")

    # Insert chunk
    df_chunk.to_sql(
        name="yellow_taxi_data",
        con=engine,
        if_exists="append"
    )

    print("Inserted:", len(df_chunk))
```

### Alternative Approach (Without First Flag)

```python
first_chunk = next(df_iter)

first_chunk.head(0).to_sql(
    name="yellow_taxi_data",
    con=engine,
    if_exists="replace"
)

print("Table created")

first_chunk.to_sql(
    name="yellow_taxi_data",
    con=engine,
    if_exists="append"
)

print("Inserted first chunk:", len(first_chunk))

for df_chunk in df_iter:
    df_chunk.to_sql(
        name="yellow_taxi_data",
        con=engine,
        if_exists="append"
    )
    print("Inserted chunk:", len(df_chunk))
```

## Adding Progress Bar

Add `tqdm` to see progress:

```bash
uv add tqdm
```

Put it around the iterable:

```python
from tqdm.auto import tqdm

for df_chunk in tqdm(df_iter):
    ...
```

## Verify the Data

Connect to it using pgcli:

```bash
uv run pgcli -h localhost -p 5432 -u root -d ny_taxi
```

And explore the data.

---



# 06 - Creating the Data Ingestion Script


Now let's convert the notebook to a Python script.

## Convert Notebook to Script

```bash
uv run jupyter nbconvert --to=script notebook.ipynb
mv notebook.py ingest_data.py
```

## The Complete Ingestion Script

See the `pipeline/` directory for the complete script with click integration. Here's the core structure:

```python
import pandas as pd
from sqlalchemy import create_engine
from tqdm.auto import tqdm

dtype = {
    "VendorID": "Int64",
    "passenger_count": "Int64",
    "trip_distance": "float64",
    "RatecodeID": "Int64",
    "store_and_fwd_flag": "string",
    "PULocationID": "Int64",
    "DOLocationID": "Int64",
    "payment_type": "Int64",
    "fare_amount": "float64",
    "extra": "float64",
    "mta_tax": "float64",
    "tip_amount": "float64",
    "tolls_amount": "float64",
    "improvement_surcharge": "float64",
    "total_amount": "float64",
    "congestion_surcharge": "float64"
}

parse_dates = [
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime"
]
```

## Click Integration

The script uses `click` for command-line argument parsing:

```python
import click

@click.command()
@click.option('--user', default='root', help='PostgreSQL user')
@click.option('--password', default='root', help='PostgreSQL password')
@click.option('--host', default='localhost', help='PostgreSQL host')
@click.option('--port', default=5432, type=int, help='PostgreSQL port')
@click.option('--db', default='ny_taxi', help='PostgreSQL database name')
@click.option('--table', default='yellow_taxi_data', help='Target table name')
def ingest_data(user, password, host, port, db, table):
    # Ingestion logic here
    pass
```

## Running the Script

The script reads data in chunks (100,000 rows at a time) to handle large files efficiently without running out of memory.

Example usage:

```bash
uv run python ingest_data.py \
  --user=root \
  --password=root \
  --host=localhost \
  --port=5432 \
  --db=ny_taxi \
  --table=yellow_taxi_trips
```

---



# 07 - pgAdmin - Database Management Tool


`pgcli` is a handy tool but it's cumbersome to use for complex queries and database management. [`pgAdmin` is a web-based tool](https://www.pgadmin.org/) that makes it more convenient to access and manage our databases.

It's possible to run pgAdmin as a container along with the Postgres container, but both containers will have to be in the same _virtual network_ so that they can find each other.

## Run pgAdmin Container

```bash
docker run -it \
  -e PGADMIN_DEFAULT_EMAIL="admin@admin.com" \
  -e PGADMIN_DEFAULT_PASSWORD="root" \
  -v pgadmin_data:/var/lib/pgadmin \
  -p 8085:80 \
  dpage/pgadmin4
```

The `-v pgadmin_data:/var/lib/pgadmin` volume mapping saves pgAdmin settings (server connections, preferences) so you don't have to reconfigure it every time you restart the container.

### Parameters Explained

* The container needs 2 environment variables: a login email and a password. We use `admin@admin.com` and `root` in this example.
* pgAdmin is a web app and its default port is 80; we map it to 8085 in our localhost to avoid any possible conflicts.
* The actual image name is `dpage/pgadmin4`.

**Note:** This won't work yet because pgAdmin can't see the PostgreSQL container. They need to be on the same Docker network!

## Docker Networks

Let's create a virtual Docker network called `pg-network`:

```bash
docker network create pg-network
```

> You can remove the network later with the command `docker network rm pg-network`. You can look at the existing networks with `docker network ls`.

### Run Containers on the Same Network

Stop both containers and re-run them with the network configuration:

```bash
# Run PostgreSQL on the network
docker run -it \
  -e POSTGRES_USER="root" \
  -e POSTGRES_PASSWORD="root" \
  -e POSTGRES_DB="ny_taxi" \
  -v ny_taxi_postgres_data:/var/lib/postgresql \
  -p 5432:5432 \
  --network=pg-network \
  --name pgdatabase \
  postgres:18

# In another terminal, run pgAdmin on the same network
docker run -it \
  -e PGADMIN_DEFAULT_EMAIL="admin@admin.com" \
  -e PGADMIN_DEFAULT_PASSWORD="root" \
  -v pgadmin_data:/var/lib/pgadmin \
  -p 8085:80 \
  --network=pg-network \
  --name pgadmin \
  dpage/pgadmin4
```

* Just like with the Postgres container, we specify a network and a name for pgAdmin.
* The container names (`pgdatabase` and `pgadmin`) allow the containers to find each other within the network.

## Connect pgAdmin to PostgreSQL

You should now be able to load pgAdmin on a web browser by browsing to `http://localhost:8085`. Use the same email and password you used for running the container to log in.

1. Open browser and go to `http://localhost:8085`
2. Login with email: `admin@admin.com`, password: `root`
3. Right-click "Servers" → Register → Server
4. Configure:
   - **General tab**: Name: `Local Docker`
   - **Connection tab**:
     - Host: `pgdatabase` (the container name)
     - Port: `5432`
     - Username: `root`
     - Password: `root`
5. Save

Now you can explore the database using the pgAdmin interface!

---



# 08 - Dockerizing the Ingestion Script

Now let's containerize the ingestion script so we can run it in Docker.

## The Dockerfile

The `pipeline/Dockerfile` shows how to containerize the ingestion script:

```dockerfile
FROM python:3.13.11-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

WORKDIR /code
ENV PATH="/code/.venv/bin:$PATH"

COPY pyproject.toml .python-version uv.lock ./
RUN uv sync --locked

COPY ingest_data.py .

ENTRYPOINT ["python", "ingest_data.py"]
```

### Explanation

- `FROM python:3.13.11-slim`: Start with slim Python 3.13 image for smaller size
- `COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/`: Copy uv binary from official uv image
- `WORKDIR /code`: Set working directory inside container
- `ENV PATH="/code/.venv/bin:$PATH"`: Add virtual environment to PATH
- `COPY pyproject.toml .python-version uv.lock ./`: Copy dependency files first (better caching)
- `RUN uv sync --locked`: Install all dependencies from lock file (ensures reproducible builds)
- `COPY ingest_data.py .`: Copy ingestion script
- `ENTRYPOINT ["python", "ingest_data.py"]`: Set entry point to run the ingestion script

## Build the Docker Image

```bash
cd pipeline
docker build -t taxi_ingest:v001 .
```

## Run the Containerized Ingestion

```bash
docker run -it \
  --network=pg-network \
  taxi_ingest:v001 \
    --user=root \
    --password=root \
    --host=pgdatabase \
    --port=5432 \
    --db=ny_taxi \
    --table=yellow_taxi_trips
```

### Important Notes

* We need to provide the network for Docker to find the Postgres container. It goes before the name of the image.
* Since Postgres is running on a separate container, the host argument will have to point to the container name of Postgres (`pgdatabase`).
* You can drop the table in pgAdmin beforehand if you want, but the script will automatically replace the pre-existing table.

---



# 09 - Docker Compose

`docker-compose` allows us to launch multiple containers using a single configuration file, so that we don't have to run multiple complex `docker run` commands separately.

Docker compose makes use of YAML files. Here's the `docker-compose.yaml` file:

```yaml
services:
  pgdatabase:
    image: postgres:18
    environment:
      POSTGRES_USER: "root"
      POSTGRES_PASSWORD: "root"
      POSTGRES_DB: "ny_taxi"
    volumes:
      - "ny_taxi_postgres_data:/var/lib/postgresql"
    ports:
      - "5432:5432"

  pgadmin:
    image: dpage/pgadmin4
    environment:
      PGADMIN_DEFAULT_EMAIL: "admin@admin.com"
      PGADMIN_DEFAULT_PASSWORD: "root"
    volumes:
      - "pgadmin_data:/var/lib/pgadmin"
    ports:
      - "8085:80"



volumes:
  ny_taxi_postgres_data:
  pgadmin_data:
```

### Explanation

* We don't have to specify a network because `docker-compose` takes care of it: every single container (or "service", as the file states) will run within the same network and will be able to find each other according to their names (`pgdatabase` and `pgadmin` in this example).
* All other details from the `docker run` commands (environment variables, volumes and ports) are mentioned accordingly in the file following YAML syntax.

## Start Services with Docker Compose

We can now run Docker compose by running the following command from the same directory where `docker-compose.yaml` is found. Make sure that all previous containers aren't running anymore:

```bash
docker-compose up
```

### Detached Mode

If you want to run the containers again in the background rather than in the foreground (thus freeing up your terminal), you can run them in detached mode:

```bash
docker-compose up -d
```

## Stop Services

You will have to press `Ctrl+C` in order to shut down the containers when running in foreground mode. The proper way of shutting them down is with this command:

```bash
docker-compose down
```

## Other Useful Commands

```bash
# View logs
docker-compose logs

# Stop and remove volumes
docker-compose down -v
```

## Benefits of Docker Compose

- Single command to start all services
- Automatic network creation
- Easy configuration management
- Declarative infrastructure

## Running the Ingestion Script with Docker Compose

If you want to re-run the dockerized ingest script when you run Postgres and pgAdmin with `docker-compose`, you will have to find the name of the virtual network that Docker compose created for the containers.

```bash
# check the network link:
docker network ls

# it's pipeline_default (or similar based on directory name)
# now run the script:
docker run -it \
  --network=pipeline_default \
  taxi_ingest:v001 \
    --user=root \
    --password=root \
    --host=pgdatabase \
    --port=5432 \
    --db=ny_taxi \
    --table=yellow_taxi_trips
```
