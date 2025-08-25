# Connecting pgAdmin and Postgres

pgAdmin provides a GUI client to manage and query Postgres databases.

---

## 1. Run pgAdmin in Docker

```bash
docker run -it -p 80:80 \
  -e PGADMIN_DEFAULT_EMAIL="admin@admin.com" \
  -e PGADMIN_DEFAULT_PASSWORD="root" \
  --network=pg-network \
  --name pgadmin-client \
  -d dpage/pgadmin4
```

Open your browser → http://localhost:80

Login with:
- Email: `admin@admin.com`
- Password: `root`

---

## 2. Network Setup

Both Postgres (`pg-database`) and pgAdmin (`pgadmin-client`) must be on the **same** Docker network.

Create a network if not already:

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
  -d postgres:13

```

Run pgAdmin (as shown above) and attach to pg-network.

---

## 3. Register Server in pgAdmin

Inside pgAdmin → **Add New Server**:

- General → Name: Local NY Taxi (could be any name.)

- Connection Tab:

    - Host name/address: `pg-database` ✅ (not localhost)
    - Port: `5432`
    - Username: `root`
    - Password: `root`
    - Maintenance DB: `ny_taxi`

### Why not `localhost`?

🔴 If you set `localhost`, pgAdmin will try to connect to itself, not Postgres.

✅ Use the container name (`pg-database`) as the host inside the Docker network.

- From **your host machine**: connect with `localhost:5432`

- From another container (**pgAdmin**): connect with `pg-database:5432`

# Quick Tests

From host machine:

```bash
pgcli -h localhost -p 5432 -U root -d ny_taxi

```

From inside pgAdmin container:

```bash
docker exec -it pgadmin-client ping pg-database

```

✅ If ping works, pgAdmin can connect to Postgres.