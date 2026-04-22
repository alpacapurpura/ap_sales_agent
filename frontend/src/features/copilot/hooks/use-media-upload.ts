"use client";

// [COPILOT-MEDIA-UPLOAD] — docs/domains/copilot/UI-SPEC.md §5
// React Query mutation hook that wraps uploadCopilotMedia (XHR-based, has progress).
// Each upload is independent — multiple files can upload in parallel.

import { useAuth } from "@clerk/nextjs";
import { useMutation } from "@tanstack/react-query";
import { useCallback, useRef, useState } from "react";

import {
  inferMediaKind,
  uploadCopilotMedia,
  validateFileSize,
  validateMimeType,
  type MediaKind,
  type MediaUploadResponse,
} from "../api/media-api";

// ── Types ────────────────────────────────────────────────────────────

export type UploadStatus = "idle" | "uploading" | "success" | "error";

export interface UploadItem {
  /** Stable client-side ID (crypto.randomUUID or fallback) */
  id: string;
  file: File;
  kind: MediaKind;
  status: UploadStatus;
  /** 0-100 during upload */
  progress: number;
  /** Populated on success */
  result?: MediaUploadResponse;
  /** Human-readable error message */
  error?: string;
}

export interface UseMediaUploadReturn {
  /** Upload a file. Returns the upload item ID. */
  uploadMedia: (file: File, kindOverride?: MediaKind) => Promise<string>;
  /** Cancel an in-flight upload by ID */
  cancelUpload: (id: string) => void;
  /** All tracked uploads */
  uploads: UploadItem[];
  /** Remove a completed/error upload from the list */
  removeUpload: (id: string) => void;
  /** Validate a file before adding it to the queue */
  validateFile: (file: File) => string | null;
}

// ── Helpers ──────────────────────────────────────────────────────────

function generateId(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `upload-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

// ── Hook ─────────────────────────────────────────────────────────────

/**
 * Manages media upload queue with per-file progress tracking.
 * Uses XMLHttpRequest (via uploadCopilotMedia) for progress events.
 * Each upload gets an AbortController for cancellation.
 */
export function useMediaUpload(): UseMediaUploadReturn {
  const { getToken } = useAuth();
  const [uploads, setUploads] = useState<UploadItem[]>([]);

  // Map of uploadId → AbortController for cancellation
  const controllersRef = useRef<Map<string, AbortController>>(new Map());

  const { mutateAsync } = useMutation({
    mutationFn: async ({
      id,
      file,
      kind,
      token,
      signal,
    }: {
      id: string;
      file: File;
      kind: MediaKind;
      token: string;
      signal: AbortSignal;
    }) => {
      return uploadCopilotMedia({
        file,
        kind,
        token,
        signal,
        onProgress: (pct) => {
          setUploads((prev) =>
            prev.map((u) => (u.id === id ? { ...u, progress: pct, status: "uploading" } : u)),
          );
        },
      });
    },
  });

  const validateFile = useCallback((file: File): string | null => {
    const mimeError = validateMimeType(file);
    if (mimeError) return mimeError;
    const kind = inferMediaKind(file.type);
    return validateFileSize(file, kind);
  }, []);

  const uploadMedia = useCallback(
    async (file: File, kindOverride?: MediaKind): Promise<string> => {
      const id = generateId();
      const kind = kindOverride ?? inferMediaKind(file.type);

      const item: UploadItem = {
        id,
        file,
        kind,
        status: "idle",
        progress: 0,
      };

      setUploads((prev) => [...prev, item]);

      const controller = new AbortController();
      controllersRef.current.set(id, controller);

      try {
        const token = await getToken();
        if (!token) throw new Error("No autenticado");

        const result = await mutateAsync({
          id,
          file,
          kind,
          token,
          signal: controller.signal,
        });

        setUploads((prev) =>
          prev.map((u) => (u.id === id ? { ...u, status: "success", progress: 100, result } : u)),
        );
      } catch (err) {
        const isAbort = err instanceof DOMException && err.name === "AbortError";
        if (!isAbort) {
          const errorMsg = err instanceof Error ? err.message : "Error al subir el archivo";
          setUploads((prev) =>
            prev.map((u) => (u.id === id ? { ...u, status: "error", error: errorMsg } : u)),
          );
        }
      } finally {
        controllersRef.current.delete(id);
      }

      return id;
    },
    [getToken, mutateAsync],
  );

  const cancelUpload = useCallback((id: string) => {
    controllersRef.current.get(id)?.abort();
    setUploads((prev) => prev.filter((u) => u.id !== id));
  }, []);

  const removeUpload = useCallback((id: string) => {
    setUploads((prev) => prev.filter((u) => u.id !== id));
  }, []);

  return { uploadMedia, cancelUpload, uploads, removeUpload, validateFile };
}
