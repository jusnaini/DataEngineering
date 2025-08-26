# About
This repository contains my personal study notes from the **Data Engineering ZoomCamp** by DataTalksClub, starting with **[01-docker-terraform]**.  

The notes are organized according to the order of tutorial videos, along with the steps I took to complete each task.  

---

# My Methodology

I first discovered this bootcamp earlier in 2025 when searching for the best way to learn Data Engineering. A Reddit thread recommended both this course and the **DeepLearning.AI Data Engineering Professional Certificate**.  

At first, I tried to follow the ZoomCamp videos directly, but I quickly got lost. It was mentally exhausting to go through the steps without fully understanding them, so I quit and switched to auditing the Coursera course. However, I struggled to stay consistent with the modules—it just didn’t stick for me.  

Eventually, I returned to the ZoomCamp with a different approach:  

1. **Read** the provided README/materials before watching the videos.  
2. **Watch** the videos with context.  
3. **Do** the tasks step by step.  
4. **Repeat** (read → watch → do → rewatch → redo).  

This iterative process not only improved my understanding but also reduced the feeling of overwhelm. Surprisingly, it also made me faster at completing the tasks.  

---

# My Setup
I’m running everything on **GitHub Codespaces** instead of my local machine.  

Since I already have a `DataEngineering` repo where I plan to store all my Data Engineering study materials, I organized everything into subfolders. For this DE ZoomCamp, I also created a separate virtual environment in the Codespaces machine:  

### 1. Create a new virtual environment  
I’m using Python 3.13:  
```bash
conda create -n zoomcamp-dev-env python=3.13
conda init
```
### 2. Restart the terminal
By default, it activates (base). Deactivate it first, then activate the new environment:

```bash
$ conda deactivate 
$ conda activate zoomcamp-dev-env
```

### 3. Optional: Simplify the terminal prompt:
`$PS1=">"` 
> This shortens the terminal display from:

```markdown
(zoomcamp-dev-env) @jusnaini ➜ /workspaces/DataEngineering (main) $
```
> to simply
```markdown
>
```

# Docker + Postgres
## [Introduction to Docker](1-Introduction-to-Docker.md)
- Why do we need Docker
- Creating a simple 'data'pipeline in Docker

## Ingesting NY Taxi Data to Postgres
- Running Postgress locally with Docker
- using `pgclic` for connecting the database
- Exploring the NY Taxi dataset
- Ingesting the data into the database

## Connecting PgAdmin and Postgres
- Using PgAdmin tool for an easier interface with Postgres database
- Dockerizing PgAdmin
- Connecting PgAdmin+Postgres with Docker networks

## Putting the ingestion script into Docker
- Converting the Jupyter notebook to a Python script
- Parameterizing the script with argparse
- Dockerizing the ingestion script

## Running Postgres and PgAdmin with Docker-Compose
- Why we need Docker Compose
- Writing a `docker-compose.yaml` file
Running multiple containers with `docker-compose up`

## SQL Refresher
- Adding the Zones table
- Inner joins
- Basic data quality checks
- Left, Right and Outer joins
- Group by

## Docker Networking and Port Mapping
- Docker networks
- Port forwarding to the host environment
- Communicating between containers in the network
- `.dockerignore` file