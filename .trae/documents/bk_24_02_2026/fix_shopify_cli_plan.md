# Plan: Fix Shopify CLI Configuration Push (Isolation Method)

## Problem
The Shopify CLI persists in crashing with `EACCES` permission errors when scanning the `data/postgres_data` directory, regardless of ignore files. This is likely due to the scanner hitting the permission block before filtering.

## Solution
We will isolate the configuration process. Since `app config push` primarily updates settings defined in `shopify.app.toml` (URLs, Auth, Webhooks), we can run this command from a clean directory that contains *only* the necessary configuration files, bypassing the problematic `data` directory entirely.

## Steps

1.  **Prepare Isolation Directory**
    - Create a directory `deploy_config/`.
    - Copy `shopify.app.toml` and `package.json` into it.
    - Copy `.gitignore` (just in case).

2.  **Install Dependencies Locally**
    - Run `npm install` inside `deploy_config/` to set up the CLI environment there.

3.  **Push Configuration**
    - Run `npx shopify app config push` from within `deploy_config/`.
    - The CLI will scan only this clean directory, encounter no permission errors, and successfully upload the config.

4.  **Cleanup**
    - Remove the `deploy_config/` directory (optional, or keep for future updates).

## Verification
- Command succeeds.
- Shopify Dashboard updates.
