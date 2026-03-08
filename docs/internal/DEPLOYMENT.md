# UATP Capsule Engine - Deployment and Operations Guide

This guide provides detailed instructions for deploying and managing the UATP Capsule Engine in a production environment.

## 1. Prerequisites

Before you begin, ensure you have the following software installed on your deployment server:

- **Git:** For cloning the repository.
- **Docker:** The container runtime. [Installation Guide](https://docs.docker.com/engine/install/)
- **Docker Compose:** For orchestrating the multi-container application. [Installation Guide](https://docs.docker.com/compose/install/)

## 2. Configuration

All configuration is managed via environment variables. The application uses a `.env` file to load these variables.

### Step 2.1: Clone the Repository

```bash
git clone https://github.com/kay/uatp-capsule-engine.git
cd uatp-capsule-engine
```

### Step 2.2: Create the `.env` File

Create a `.env` file by copying the provided example:

```bash
cp .env.example .env
```

### Step 2.3: Populate `.env` with Secrets

Open the `.env` file and fill in the required values. **It is critical to use strong, randomly generated secrets for a production environment.**

- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`: Credentials for the PostgreSQL database.
- `UATP_SIGNING_KEY`: A **64-character hexadecimal** string used for signing capsules.
- `UATP_API_KEYS`: A JSON string defining the API keys and their associated permissions (e.g., `read`, `write`).

**Example `UATP_API_KEYS` format:**
```json
'{"your-read-key-here": {"scopes": ["read"]}, "your-write-key-here": {"scopes": ["write"]}}'
```

## 3. Deployment

The application is deployed as a set of Docker containers orchestrated by Docker Compose.

To build and start all services in detached mode, run:

```bash
docker-compose up --build -d
```

## 4. Verification

After deployment, verify that all services are running and healthy.

- **Check Container Status:**
  ```bash
  docker-compose ps
  ```
  All services (`api`, `postgres`, `prometheus`, `grafana`, `backup`) should show a status of `Up` or `Running`.

- **API Health Check:**
  Access the health check endpoint. It should return a `200 OK` status.
  ```bash
  curl http://localhost:9090/health
  ```

- **API Documentation:**
  The interactive API documentation is available at [http://localhost:9090/docs](http://localhost:9090/docs).

## 5. Operations

### Monitoring

The monitoring stack provides visibility into the application's performance.

- **Prometheus:** View service discovery targets and metrics at [http://localhost:9091](http://localhost:9091).
- **Grafana:** Access the pre-configured dashboard at [http://localhost:3000](http://localhost:3000) (Login: `admin` / `admin`).

### Database Migrations (Alembic)

If the database schema changes, you will need to apply migrations.

1.  **Generate a new migration script (if you've changed `src/models.py`):
    ```bash
    docker-compose exec api alembic revision --autogenerate -m "Your migration message"
    ```

2.  **Apply migrations:**
    ```bash
    docker-compose exec api alembic upgrade head
    ```

### Backup and Recovery

#### Manual Backups

A daily backup service is configured to run automatically. To perform a manual backup at any time, execute the backup script:

```bash
docker-compose exec backup /app/scripts/backup.sh
```

Backups are stored in the `backups` directory on the host in `.sql.gz` format.

#### Disaster Recovery (Restoring from Backup)

To restore the database from a backup file, follow these steps. This procedure will overwrite the current database with the contents of the backup file.

1.  **Identify the backup file:** Choose the backup file you want to restore from the `backups/` directory. For example, `backup_2025-07-08_21-45-00.sql.gz`.

2.  **Stop the API service** to prevent any new data from being written during the restore process:
    ```bash
    docker-compose stop api
    ```

3.  **Restore the database:** Execute the following command, replacing `BACKUP_FILENAME.sql.gz` with your chosen backup file. This command will:
    - `gunzip` the compressed backup file.
    - Pipe the SQL commands to `psql` running inside the `postgres` container.
    - The `psql` command first drops the existing public schema (deleting all tables) and then recreates it before restoring the data.

    ```bash
    gunzip < backups/BACKUP_FILENAME.sql.gz | docker-compose exec -T postgres psql -U testuser -d testdb -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" -c "\\i /dev/stdin"
    ```
    **Note:** Replace `testuser` and `testdb` if you have changed them in your `.env` file.

4.  **Restart the API service:**
    ```bash
    docker-compose start api
    ```

5.  **Verify the restore:** Check the application to ensure the data has been restored correctly.

### Stopping the Application

To stop all services, run:

```bash
docker-compose down
```

To stop and remove all associated volumes (including the database), use:

```bash
docker-compose down -v
```

## 6. Performance Tuning

The performance of the database connection pool can be tuned via environment variables. The optimal values will depend on the expected load and the resources available to your database server.

- `UATP_DB_POOL_SIZE`: The number of connections to keep open in the pool. Default: `5`.
- `UATP_DB_MAX_OVERFLOW`: The number of additional connections that can be opened beyond the pool size under heavy load. Default: `10`.
- `UATP_DB_POOL_RECYCLE`: The number of seconds after which a connection is automatically recycled. This is useful for preventing issues with stale connections. Default: `3600` (1 hour).

These variables can be set in your `.env` file.

## 7. Troubleshooting

- **`ImportError` or `ModuleNotFoundError`:** Rebuild your Docker images with `docker-compose up --build -d` to ensure all dependencies are correctly installed.
- **API Connection Issues:** Ensure the API is bound to `0.0.0.0` in `docker-compose.yml` to be accessible from outside the container.
- **Permission Denied:** Check file permissions on mounted volumes, especially for the `backups` directory.
