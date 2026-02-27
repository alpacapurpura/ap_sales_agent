The error is caused by `tailwindcss: "latest"` in `package.json` pulling in Tailwind CSS v4.0, which has changed how it integrates with PostCSS. The error message provides the exact fix required.

## Proposed Solution

### 1. Update `package.json`

* Add `@tailwindcss/postcss` to `devDependencies`.

* (Optional but recommended) Pin versions to avoid future "latest" surprises, but I will stick to fixing the immediate error first.

### 2. Update `postcss.config.js`

* Change the plugin from `tailwindcss` to `@tailwindcss/postcss`.

### 3. Rebuild Container

* Rebuild the `client_dashboard` container to install the new dependency and apply the config.

### 4. Verify

* Check logs to ensure the build succeeds.

