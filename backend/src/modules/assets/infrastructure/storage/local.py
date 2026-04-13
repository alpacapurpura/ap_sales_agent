"""Local infrastructure."""

import shutil
import uuid
from pathlib import Path
from typing import BinaryIO

from src.core.config import settings

from .base import StorageStrategy


class LocalStorageStrategy(StorageStrategy):
    """Implement local storage storage strategy."""

    def __init__(self, upload_dir: str = settings.UPLOAD_DIR) -> None:
        """Initialize LocalStorageStrategy."""
        self.upload_dir = upload_dir
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)

    def save(
        self,
        file_obj: BinaryIO,
        filename: str,
        path_prefix: str = "",
    ) -> tuple[str, str]:
        """Persist the entity to the database."""
        # Generate safe filename
        ext = Path(filename).suffix
        unique_name = f"{uuid.uuid4()}{ext}"

        # Determine full path
        # When path_prefix is provided, creates subdirectories under upload_dir

        relative_path = str(Path(path_prefix) / unique_name) if path_prefix else unique_name
        full_path = str(Path(self.upload_dir) / relative_path)

        # Ensure directory exists
        Path(full_path).parent.mkdir(parents=True, exist_ok=True)

        # Write file
        with Path(full_path).open("wb") as buffer:
            shutil.copyfileobj(file_obj, buffer)

        # Construct public URL
        # Assumes 'static' is mounted at /static
        # UPLOAD_DIR is 'static/uploads', so public url is /static/uploads/...
        # We need to strip the 'static/' part if it's already in the mount path logic?
        # In main.py: app.mount("/static", StaticFiles(directory="static"), name="static")
        # So if file is at static/uploads/foo.png, url is /static/uploads/foo.png

        # Normalize paths for URL (replace backslashes on Windows)
        url_path = str(Path(self.upload_dir) / relative_path).replace("\\", "/")
        if not url_path.startswith("/"):
            url_path = "/" + url_path

        return full_path, url_path

    def get_file_bytes(self, storage_path: str) -> bytes:
        """Retrieve file bytes."""
        return Path(storage_path).read_bytes()

    def delete(self, storage_path: str) -> bool:
        """Handle delete operation."""
        try:
            p = Path(storage_path)
            if p.exists():
                p.unlink()
        except OSError:
            return False
        else:
            return True
