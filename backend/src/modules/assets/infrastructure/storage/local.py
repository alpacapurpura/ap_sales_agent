import os
import shutil
import uuid
from typing import BinaryIO, Tuple
from src.core.config import settings
from .base import StorageStrategy

class LocalStorageStrategy(StorageStrategy):
    def __init__(self, upload_dir: str = settings.UPLOAD_DIR):
        self.upload_dir = upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)

    def save(self, file_obj: BinaryIO, filename: str, path_prefix: str = "") -> Tuple[str, str]:
        # Generate safe filename
        ext = os.path.splitext(filename)[1]
        unique_name = f"{uuid.uuid4()}{ext}"
        
        # Determine full path
        # If path_prefix is provided, create subdirectories
        # Example: static/uploads/tenant_id/image.png
        
        relative_path = os.path.join(path_prefix, unique_name) if path_prefix else unique_name
        full_path = os.path.join(self.upload_dir, relative_path)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Write file
        with open(full_path, "wb") as buffer:
            shutil.copyfileobj(file_obj, buffer)
            
        # Construct public URL
        # Assumes 'static' is mounted at /static
        # UPLOAD_DIR is 'static/uploads', so public url is /static/uploads/...
        # We need to strip the 'static/' part if it's already in the mount path logic?
        # In main.py: app.mount("/static", StaticFiles(directory="static"), name="static")
        # So if file is at static/uploads/foo.png, url is /static/uploads/foo.png
        
        # Normalize paths for URL (replace backslashes on Windows)
        url_path = os.path.join(self.upload_dir, relative_path).replace("\\", "/")
        if not url_path.startswith("/"):
            url_path = "/" + url_path
            
        return full_path, url_path

    def get_file_bytes(self, storage_path: str) -> bytes:
        with open(storage_path, "rb") as f:
            return f.read()

    def delete(self, storage_path: str) -> bool:
        try:
            if os.path.exists(storage_path):
                os.remove(storage_path)
            return True
        except Exception:
            return False
