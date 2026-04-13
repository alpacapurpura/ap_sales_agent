"""
Migration script: Move existing LOCAL assets to Cloudflare R2.

Usage (inside container):
    docker exec -it visionarias_brain_dev python src/scripts/migrate_local_to_r2.py

Prerequisites:
    - R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY must be set in .env
    - STORAGE_PROVIDER=R2 in .env (or run with --dry-run to preview)

What it does:
    1. Finds all assets in DB with storage_provider = 'LOCAL'
    2. Reads each file from local storage_path
    3. Uploads to R2 using the same key structure
    4. Updates DB: storage_provider=R2, storage_path=key, public_url=R2 URL
    5. On success, deletes local file

Run with --dry-run to preview without making changes.
"""

import argparse
import sys
from pathlib import Path

current_dir = Path(__file__).resolve().parent
backend_dir = (current_dir / "../../").resolve()
sys.path.insert(0, str(backend_dir))

from src.core.config import settings
from src.core.database import SessionLocal
from src.modules.assets.infrastructure.models.asset_model import (
    AssetModel,
)
from src.modules.assets.infrastructure.storage.r2 import R2StorageStrategy


def migrate(dry_run: bool = False):
    print(f"{'[DRY RUN] ' if dry_run else ''}Starting LOCAL → R2 asset migration...")
    print(f"  Bucket:     {settings.R2_BUCKET_NAME}")
    print(f"  Endpoint:   {settings.R2_ENDPOINT_URL}")
    print(f"  Public URL: {settings.R2_PUBLIC_URL}")
    print()

    if not settings.R2_ACCESS_KEY_ID or settings.R2_ACCESS_KEY_ID.startswith(
        "PENDIENTE",
    ):
        print("❌ R2_ACCESS_KEY_ID not configured. Set it in .env first.")
        sys.exit(1)

    r2 = R2StorageStrategy()
    db = SessionLocal()

    try:
        assets = db.query(AssetModel).filter(AssetModel.storage_provider == "LOCAL").all()
        print(f"Found {len(assets)} local asset(s) to migrate.\n")

        success = 0
        skipped = 0
        failed = 0

        for asset in assets:
            local_path = asset.storage_path
            if not local_path or not Path(local_path).exists():
                print(f"  ⚠️  SKIP  {asset.id} — file not found at: {local_path}")
                skipped += 1
                continue

            # Build R2 key from local path.
            # Handles both legacy (/app/static/{tenant}/...) and current (/app/static/uploads/...)
            # Strip the leading /app/ so we keep the rest as the key.
            rel = local_path
            for prefix in ["/app/", "app/"]:
                if local_path.startswith(prefix):
                    rel = local_path[len(prefix) :]
                    break
            # rel is now e.g. "static/uploads/tenant/image/uuid.png"
            # or legacy "static/tenant/offers/.../gallery/uuid.jpeg"

            r2_key = rel
            r2_public_url = f"{settings.R2_PUBLIC_URL.rstrip('/')}/{r2_key}"

            print(f"  → {asset.id}")
            print(f"     local:  {local_path}")
            print(f"     r2 key: {r2_key}")
            print(f"     url:    {r2_public_url}")

            if dry_run:
                print("     [DRY RUN] Skipping upload.\n")
                continue

            try:
                with Path(local_path).open("rb") as f:
                    r2.client.put_object(
                        Bucket=r2.bucket,
                        Key=r2_key,
                        Body=f.read(),
                    )

                # Update DB
                db.query(AssetModel).filter(AssetModel.id == asset.id).update(
                    {
                        "storage_provider": "R2",
                        "storage_path": r2_key,
                        "public_url": r2_public_url,
                    },
                )
                db.commit()

                # Remove local file
                Path(local_path).unlink()
                print("     ✅ Migrated & local file deleted.\n")
                success += 1

            except Exception as e:  # noqa: BLE001 — migration script resilience
                db.rollback()
                print(f"     ❌ FAILED: {e}\n")
                failed += 1

        print("\nMigration complete:")
        print(f"  ✅ Migrated: {success}")
        print(f"  ⚠️  Skipped:  {skipped}")
        print(f"  ❌ Failed:   {failed}")

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Migrate local assets to Cloudflare R2",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview only, no changes",
    )
    args = parser.parse_args()
    migrate(dry_run=args.dry_run)
