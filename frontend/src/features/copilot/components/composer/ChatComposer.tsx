"use client";

// [COPILOT-COMPOSER] — docs/domains/copilot/UI-SPEC.md §3
// Compound composer component. Sub-components accessible as ChatComposer.X.

import { useCallback, useReducer } from "react";

import { cn } from "@/lib/utils";

import { useMediaUpload } from "../../hooks/use-media-upload";
import { useVoiceRecorder } from "../../hooks/use-voice-recorder";

import { AttachmentTray } from "./AttachmentTray";
import { ComposerContextChips } from "./ComposerContextChips";
import { ReplyPreview } from "./ReplyPreview";
import { SuggestedChips } from "./SuggestedChips";
import { Toolbar } from "./Toolbar";
import { VoiceOverlay } from "./VoiceOverlay";

import type { AttachmentChipFile } from "./AttachmentChip";
import type { ReplyRef } from "./ReplyPreview";
import type { SelectedField } from "../../store/copilot-store";
import type { MessageBlock } from "../../types/message-blocks";
import type { Suggestion } from "../../types/suggestions";

// ── State ────────────────────────────────────────────────────────────

interface ComposerState {
  draft: string;
  attachments: AttachmentChipFile[];
  replyTo: ReplyRef | null;
}

type ComposerAction =
  | { type: "SET_DRAFT"; payload: string }
  | { type: "ADD_ATTACHMENT"; payload: AttachmentChipFile }
  | { type: "UPDATE_ATTACHMENT"; payload: Partial<AttachmentChipFile> & { id: string } }
  | { type: "REMOVE_ATTACHMENT"; payload: string }
  | { type: "SET_REPLY_TO"; payload: ReplyRef | null }
  | { type: "RESET" };

function composerReducer(state: ComposerState, action: ComposerAction): ComposerState {
  switch (action.type) {
    case "SET_DRAFT":
      return { ...state, draft: action.payload };

    case "ADD_ATTACHMENT":
      return { ...state, attachments: [...state.attachments, action.payload] };

    case "UPDATE_ATTACHMENT":
      return {
        ...state,
        attachments: state.attachments.map((a) =>
          a.id === action.payload.id ? { ...a, ...action.payload } : a,
        ),
      };

    case "REMOVE_ATTACHMENT":
      return {
        ...state,
        attachments: state.attachments.filter((a) => a.id !== action.payload),
      };

    case "SET_REPLY_TO":
      return { ...state, replyTo: action.payload };

    case "RESET":
      return { draft: "", attachments: [], replyTo: null };

    default:
      return state;
  }
}

const initialState: ComposerState = {
  draft: "",
  attachments: [],
  replyTo: null,
};

// ── Types ────────────────────────────────────────────────────────────

interface ChatComposerProps extends React.HTMLAttributes<HTMLDivElement> {
  onSend: (text: string, blocks: MessageBlock[], replyTo?: ReplyRef) => void;
  disabled?: boolean;
  suggestions?: Suggestion[];
  selectedFields?: SelectedField[];
  onAttachmentsChanged?: (attachments: AttachmentChipFile[]) => void;
  /** Externally controlled replyTo (used when parent sets reply via message context menu) */
  replyTo?: ReplyRef | null;
  onClearReply?: () => void;
}

// ── Component ────────────────────────────────────────────────────────

/**
 *
 */
function ChatComposerRoot({
  onSend,
  disabled = false,
  onAttachmentsChanged,
  replyTo: externalReplyTo,
  onClearReply,
  className,
  ...props
}: ChatComposerProps) {
  const [state, dispatch] = useReducer(composerReducer, initialState);

  const { uploadMedia, cancelUpload } = useMediaUpload();

  const { isRecording, isTranscribing, startRecording, stopRecording, cancelRecording, duration } =
    useVoiceRecorder();

  // Use external replyTo if provided, otherwise internal state
  const activeReplyTo = externalReplyTo !== undefined ? externalReplyTo : state.replyTo;

  const handleDraftChange = useCallback((value: string) => {
    dispatch({ type: "SET_DRAFT", payload: value });
  }, []);

  const handleChipClick = useCallback((prompt: string) => {
    dispatch({ type: "SET_DRAFT", payload: prompt });
  }, []);

  const handleFilesSelected = useCallback(
    async (files: File[]) => {
      for (const file of files) {
        const id = crypto.randomUUID();
        const chipFile: AttachmentChipFile = {
          id,
          file,
          status: "pending",
          progress: 0,
        };
        dispatch({ type: "ADD_ATTACHMENT", payload: chipFile });
        onAttachmentsChanged?.([...state.attachments, chipFile]);

        // Start upload
        dispatch({ type: "UPDATE_ATTACHMENT", payload: { id, status: "uploading" } });
        try {
          const uploadedId = await uploadMedia(file);
          // uploadMedia manages progress internally; mark as uploaded
          dispatch({
            type: "UPDATE_ATTACHMENT",
            payload: { id: uploadedId, status: "uploaded", progress: 100 },
          });
        } catch {
          dispatch({
            type: "UPDATE_ATTACHMENT",
            payload: { id, status: "error", error: "Error al subir" },
          });
        }
      }
    },
    [state.attachments, uploadMedia, onAttachmentsChanged],
  );

  const handleCancel = useCallback(
    (id: string) => {
      cancelUpload(id);
      dispatch({ type: "REMOVE_ATTACHMENT", payload: id });
    },
    [cancelUpload],
  );

  const handleRemove = useCallback((id: string) => {
    dispatch({ type: "REMOVE_ATTACHMENT", payload: id });
  }, []);

  const handleMicClick = useCallback(async () => {
    if (isRecording) {
      await stopRecording();
    } else {
      await startRecording();
    }
  }, [isRecording, startRecording, stopRecording]);

  const handleVoiceStop = useCallback(async () => {
    const transcript = await stopRecording();
    if (transcript) {
      dispatch({ type: "SET_DRAFT", payload: transcript });
    }
  }, [stopRecording]);

  const handleSend = useCallback(() => {
    const trimmed = state.draft.trim();
    const hasUploading = state.attachments.some(
      (a) => a.status === "pending" || a.status === "uploading",
    );

    if (!trimmed && state.attachments.length === 0) return;
    if (disabled || isRecording || isTranscribing) return;
    if (hasUploading) return;

    // Build blocks array
    const blocks: MessageBlock[] = [];

    // Quote reply first
    if (activeReplyTo) {
      blocks.push({
        id: crypto.randomUUID(),
        type: "quote_reply",
        ref_message_id: activeReplyTo.messageId,
        preview: activeReplyTo.preview,
        ref_author_role: activeReplyTo.role,
      });
    }

    // Text block
    if (trimmed) {
      blocks.push({
        id: crypto.randomUUID(),
        type: "text",
        markdown: trimmed,
      });
    }

    // Attachment blocks
    for (const att of state.attachments) {
      if (att.status !== "uploaded" || !att.result) continue;
      const { mime } = att.result;
      if (mime.startsWith("image/")) {
        blocks.push({
          id: crypto.randomUUID(),
          type: "image",
          asset_id: att.result.asset_id,
          url: att.result.public_url,
          mime,
        });
      } else if (mime.startsWith("audio/")) {
        blocks.push({
          id: crypto.randomUUID(),
          type: "audio",
          asset_id: att.result.asset_id,
          url: att.result.public_url,
          mime,
          transcript: "",
        });
      } else if (mime.startsWith("video/")) {
        blocks.push({
          id: crypto.randomUUID(),
          type: "video",
          asset_id: att.result.asset_id,
          url: att.result.public_url,
          mime,
        });
      } else {
        blocks.push({
          id: crypto.randomUUID(),
          type: "document",
          asset_id: att.result.asset_id,
          url: att.result.public_url,
          mime,
          filename: att.file.name,
          size_bytes: att.file.size,
        });
      }
    }

    onSend(trimmed, blocks, activeReplyTo ?? undefined);
    dispatch({ type: "RESET" });
    onClearReply?.();
  }, [
    state.draft,
    state.attachments,
    activeReplyTo,
    disabled,
    isRecording,
    isTranscribing,
    onSend,
    onClearReply,
  ]);

  const handleCancelReply = useCallback(() => {
    dispatch({ type: "SET_REPLY_TO", payload: null });
    onClearReply?.();
  }, [onClearReply]);

  const showVoiceOverlay = isRecording || isTranscribing;

  return (
    <div className={cn("flex flex-col border-t border-border bg-background", className)} {...props}>
      {/* [COPILOT-SUGGESTIONS-ENGINE] */}
      <ChatComposerRoot.SuggestedChips onChipClick={handleChipClick} />

      {/* Reply preview strip */}
      {activeReplyTo && (
        <ChatComposerRoot.ReplyPreview replyTo={activeReplyTo} onCancel={handleCancelReply} />
      )}

      {/* Context chips from selected form fields */}
      <ChatComposerRoot.ContextChips />

      {/* Attachment tray */}
      <ChatComposerRoot.AttachmentTray
        attachments={state.attachments}
        onCancel={handleCancel}
        onRemove={handleRemove}
      />

      {/* Voice overlay shown while recording/transcribing */}
      {showVoiceOverlay && (
        <ChatComposerRoot.VoiceOverlay
          duration={duration}
          isTranscribing={isTranscribing}
          onCancel={cancelRecording}
          onStop={handleVoiceStop}
        />
      )}

      {/* Main toolbar — hidden during voice overlay on small screens but always present */}
      {!showVoiceOverlay && (
        <ChatComposerRoot.Toolbar
          value={state.draft}
          onChange={handleDraftChange}
          onSend={handleSend}
          onFilesSelected={handleFilesSelected}
          onMicClick={handleMicClick}
          isRecording={isRecording}
          isTranscribing={isTranscribing}
          disabled={disabled}
        />
      )}
    </div>
  );
}

ChatComposerRoot.displayName = "ChatComposer";

// ── Compound namespace ────────────────────────────────────────────────

// Attach sub-components as static properties for compound component pattern
ChatComposerRoot.SuggestedChips = SuggestedChips;
ChatComposerRoot.ReplyPreview = ReplyPreview;
ChatComposerRoot.ContextChips = ComposerContextChips;
ChatComposerRoot.AttachmentTray = AttachmentTray;
ChatComposerRoot.Toolbar = Toolbar;
ChatComposerRoot.VoiceOverlay = VoiceOverlay;

export { ChatComposerRoot as ChatComposer };
