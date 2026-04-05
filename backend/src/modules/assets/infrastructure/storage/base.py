from abc import ABC, abstractmethod
from typing import BinaryIO


class StorageStrategy(ABC):
    @abstractmethod
    def get_file_bytes(self, storage_path: str) -> bytes:
        """
        Read file bytes from storage.

        Args:
            storage_path: The internal path/key returned by save().

        Returns:
            bytes: Raw file content.
        """

    @abstractmethod
    def save(
        self, file_obj: BinaryIO, filename: str, path_prefix: str = ""
    ) -> tuple[str, str]:
        """
        Save a file to storage.

        Args:
            file_obj: The file-like object to save.
            filename: The original filename.
            path_prefix: Optional directory/prefix (e.g., 'tenant_id/images').

        Returns:
            Tuple[str, str]: (storage_path, public_url)
            - storage_path: Internal path or key (e.g., local path or S3 key).
            - public_url: Accessible URL for the file.
        """

    @abstractmethod
    def delete(self, storage_path: str) -> bool:
        """
        Delete a file from storage.

        Args:
            storage_path: The internal path/key returned by save().

        Returns:
            bool: True if deleted or didn't exist, False on error.
        """
