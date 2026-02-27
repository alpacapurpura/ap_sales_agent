I will proceed with updating the Node.js version to the latest requested by you (version 25-alpine).

## Implementation Steps

### 1. Update Dockerfile
- Modify `frontend/Dockerfile` to use `FROM node:25-alpine` as requested.

### 2. Rebuild Container
- Execute `docker compose up -d --build client_dashboard` to apply the change.

### 3. Verification
- Check logs to confirm the service starts successfully.
- Verify that `localhost:3000` is accessible.

*Note: If `node:25-alpine` is not yet available in the Docker registry, I will fall back to the latest available version (likely `node:24-alpine` or `node:23-alpine`) and let you know.*