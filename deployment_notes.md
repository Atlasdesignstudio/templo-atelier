# Deployment Notes: Templo Atelier vFinal

## Docker Deployment (Localhost)

When running the system via `docker-compose up` on macOS, you may encounter a **500 Internal Server Error** when creating projects.

**Error:**
`sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) attempt to write a readonly database`

**Cause:**
The SQLite database file (`studio.db`) created on the host machine (by the user) has ownership/permissions that conflict with the user running inside the Docker container. Even with volume mounts, SQLite requires write access to the *directory* containing the DB file to create journal files (`-shm`, `-wal`).

**Solution:**
1.  **Stop Containers**:
    ```bash
    docker-compose down
    ```
2.  **Adjust Permissions**:
    Ensure the `scratch` directory is writable by the Docker user.
    ```bash
    chmod 777 .
    chmod 777 studio.db*
    ```
    *(Note: `777` is permissive; in production, use correct UID mapping)*.

3.  **Use Host Networking (Alternative)**:
    If utilizing `uvicorn` directly on the host (outside Docker), the issue disappears as the user matches.
    ```bash
    ./venv/bin/uvicorn src.dashboard_api.main:app --reload --port 8000
    ```

## Verification Status
- **Codebase Integration**: Checked and Verified locally (`verify_integration.py`).
- **End-to-End API**: Verified via unit tests, but blocked on Docker by permission issue.
