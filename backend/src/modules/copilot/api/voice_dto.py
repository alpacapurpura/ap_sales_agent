"""DTOs for the voice transcription API."""

from pydantic import BaseModel, ConfigDict

from src.modules.copilot.domain.message_blocks import AudioBlock


class TranscriptionResponse(BaseModel):
    """Response model for the legacy /transcribe endpoint."""

    model_config = ConfigDict(from_attributes=True)

    text: str
    language: str
    duration_seconds: float


class VoiceUploadAndTranscribeResponse(BaseModel):
    """Response model for POST /voice/upload-and-transcribe.

    # [COPILOT-VOICE-DUAL-MODE] → docs/domains/copilot/CONTRACT-MULTIMODAL.md §9

    Returns a complete AudioBlock ready to include in message.blocks[].
    The block always has both url (for playback) and transcript (for accessibility).
    transcript may be an empty string if STT failed (not null — invariant §9.6).
    """

    model_config = ConfigDict(from_attributes=True)

    block: AudioBlock
