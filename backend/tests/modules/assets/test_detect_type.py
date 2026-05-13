"""Tests for AssetsService._detect_type — pure MIME → AssetType mapping."""

from luana_core_assets.application.assets_service import AssetsService
from luana_core_assets.domain.enums import AssetType


def detect_type(mime_type: str) -> AssetType:
    """Call the private helper without constructing a full service."""
    # We instantiate without a db by bypassing __init__; the method is pure.
    svc = object.__new__(AssetsService)
    return svc._detect_type(mime_type)


class TestDetectType:
    # ---- Image types ----

    def test_image_png(self):
        assert detect_type("image/png") == AssetType.IMAGE

    def test_image_jpeg(self):
        assert detect_type("image/jpeg") == AssetType.IMAGE

    def test_image_webp(self):
        assert detect_type("image/webp") == AssetType.IMAGE

    # ---- Video types ----

    def test_video_mp4(self):
        assert detect_type("video/mp4") == AssetType.VIDEO

    def test_video_quicktime(self):
        assert detect_type("video/quicktime") == AssetType.VIDEO

    # ---- Audio types ----

    def test_audio_mpeg(self):
        assert detect_type("audio/mpeg") == AssetType.AUDIO

    def test_audio_wav(self):
        assert detect_type("audio/wav") == AssetType.AUDIO

    # ---- Document / fallback ----

    def test_pdf_is_document(self):
        assert detect_type("application/pdf") == AssetType.DOCUMENT

    def test_octet_stream_is_document(self):
        assert detect_type("application/octet-stream") == AssetType.DOCUMENT

    def test_unknown_mime_is_document(self):
        assert detect_type("application/x-totally-unknown") == AssetType.DOCUMENT
