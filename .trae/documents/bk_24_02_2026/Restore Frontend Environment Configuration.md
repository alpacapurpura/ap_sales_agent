The reason you need a `.env` in the `frontend` directory is that **Next.js**, when running locally (e.g., `npm run dev` or `npm run lint`), **only looks for environment variables in its own directory** (`frontend/`). It does not automatically look in the parent folder (`../`).

While Docker handles this mapping for you in containers (via `docker-compose.yml`), your local tools/scripts are "blind" to the root configuration.

**Solution: Single Source of Truth via Symlink**
To respect your preference for a **single `.env` file**, the best technical solution is to create a **Symbolic Link** (shortcut) inside `frontend/` that points to the root `.env`.

**Revised Plan:**
1.  **Create Symlink:** Run `ln -s ../.env .env` inside the `frontend/` directory.
    *   **Why:** This makes the root `.env` file "appear" inside the frontend folder.
    *   **Benefit:** You strictly maintain **one** file (in the root). Any change there is instantly reflected in the frontend, satisfying both Next.js requirements and your architectural preference.

This will instantly fix the `NEXT_PUBLIC_API_URL` availability for your local setup without duplicating files.