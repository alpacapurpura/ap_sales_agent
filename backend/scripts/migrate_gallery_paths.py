import shutil
from pathlib import Path

import structlog
from sqlalchemy.orm import Session
from src.modules.gallery.domain.entity import GalleryImage

from src.core.database import SessionLocal
from src.modules.offer.domain.offer_gallery import OfferGalleryImage

logger = structlog.get_logger()

BASE_STATIC_DIR = Path("static")
OLD_GALLERY_DIR = BASE_STATIC_DIR / "gallery"
OLD_OFFER_DIR = BASE_STATIC_DIR / "offers"


def migrate_brand_gallery(db: Session):
    logger.info("migration_brand_gallery_started")
    images = db.query(GalleryImage).all()

    for img in images:
        if not img.tenant_id:
            logger.warning("skipping_image_no_tenant", image_id=str(img.id))
            continue

        tenant_id = str(img.tenant_id)

        # New Path: static/{tenant_id}/brand/gallery/{filename}
        # Old Path: static/gallery/{tenant_id}_{uuid}.ext OR just {filename}

        # Determine old path logic
        # Current logic used {tenant_id}_{uuid} in filename
        # But we want to strip tenant_id prefix if we move to folder

        current_path = Path(img.file_path)
        if not current_path.exists():
            # Try relative path if absolute failed
            relative_path = Path(img.public_url.lstrip("/"))
            if (BASE_STATIC_DIR / ".." / relative_path).resolve().exists():
                current_path = (BASE_STATIC_DIR / ".." / relative_path).resolve()
            elif (Path("backend") / relative_path).exists():
                current_path = Path("backend") / relative_path
            else:
                logger.warning("source_file_not_found", path=img.file_path)
                continue

        # Target Directory
        target_dir = BASE_STATIC_DIR / tenant_id / "brand" / "gallery"
        target_dir.mkdir(parents=True, exist_ok=True)

        # Target Filename (Clean up tenant prefix if present to avoid redundancy, or keep unique)
        # Let's keep original filename to avoid DB mismatch complexity,
        # unless we want to rename. For safety, we keep filename but move folder.
        target_path = target_dir / current_path.name

        # Move file
        try:
            shutil.move(str(current_path), str(target_path))

            # Update DB
            new_public_url = f"/static/{tenant_id}/brand/gallery/{current_path.name}"
            img.file_path = str(target_path.absolute())
            img.public_url = new_public_url
            db.add(img)

            logger.info("migrated_brand_image", image_id=str(img.id))
        except Exception as e:
            logger.error("migration_failed_for_image", image_id=str(img.id), error=str(e))

    db.commit()
    logger.info("migration_brand_gallery_completed")


def migrate_offer_gallery(db: Session):
    logger.info("migration_offer_gallery_started")
    # This is trickier because old structure was static/offers/{offer_id}/gallery
    # We want static/{tenant_id}/offers/{offer_id}/gallery

    images = db.query(OfferGalleryImage).all()

    for img in images:
        if not img.tenant_id or not img.offer_id:
            continue

        tenant_id = str(img.tenant_id)
        offer_id = str(img.offer_id)

        current_path = Path(img.file_path)
        if not current_path.exists():
            continue

        # Target
        target_dir = BASE_STATIC_DIR / tenant_id / "offers" / offer_id / "gallery"
        target_dir.mkdir(parents=True, exist_ok=True)

        target_path = target_dir / current_path.name

        if current_path.absolute() == target_path.absolute():
            continue  # Already in place

        try:
            shutil.move(str(current_path), str(target_path))

            # Update DB
            new_public_url = f"/static/{tenant_id}/offers/{offer_id}/gallery/{current_path.name}"
            img.file_path = str(target_path.absolute())
            img.public_url = new_public_url
            db.add(img)

            logger.info("migrated_offer_image", image_id=str(img.id))
        except Exception as e:
            logger.error("migration_failed_for_offer_image", image_id=str(img.id), error=str(e))

    db.commit()
    logger.info("migration_offer_gallery_completed")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        migrate_brand_gallery(db)
        migrate_offer_gallery(db)
    finally:
        db.close()
