// [COPILOT-MEDIA-UPLOAD] → docs/domains/copilot/CONTRACT-MULTIMODAL.md §7
// Upload media files to the copilot media endpoint.
// Uses XMLHttpRequest (not fetch) to get progress events.

import { config } from "@/lib/config";

import { getCopilotHeaders } from "./copilot-api";

const API_URL = config.api.baseUrl;

export interface MediaUploadResponse {
  asset_id: string;
  public_url: string;
  mime: string;
  size_bytes: number;
  kind: "image" | "audio" | "video" | "document";
}

export type MediaKind = "image" | "audio" | "video" | "document";

/**
 * Upload a file to the copilot media endpoint with progress tracking.
 * Uses XMLHttpRequest for upload progress events (fetch does not support onprogress).
 *
 * [COPILOT-VOICE-UPLOAD] — audio blobs follow this same path for the dual-mode voice flow.
 */
export interface UploadCopilotMediaOptions {
  file: File;
  token: string;
  onProgress: (pct: number) => void;
  kind?: MediaKind;
  signal?: AbortSignal;
}

/**
 *
 */
export function uploadCopilotMedia({
  file,
  kind,
  onProgress,
  token,
  signal,
}: UploadCopilotMediaOptions): Promise<MediaUploadResponse> {
  return new Promise((resolve, reject) => {
    const fd = new FormData();
    fd.append("file", file);
    if (kind) fd.append("kind", kind);

    const xhr = new XMLHttpRequest();

    // Abort signal integration
    if (signal) {
      if (signal.aborted) {
        reject(new DOMException("Aborted", "AbortError"));
        return;
      }
      signal.addEventListener("abort", () => {
        xhr.abort();
        reject(new DOMException("Aborted", "AbortError"));
      });
    }

    xhr.upload.addEventListener("progress", (e) => {
      if (e.lengthComputable) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    });

    xhr.addEventListener("load", () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const data = JSON.parse(xhr.responseText) as MediaUploadResponse;
          onProgress(100);
          resolve(data);
        } catch {
          reject(new Error("Invalid JSON response from media upload"));
        }
      } else {
        reject(new Error(`Upload failed: ${xhr.status} ${xhr.statusText}`));
      }
    });

    xhr.addEventListener("error", () => {
      reject(new Error("Network error during upload"));
    });

    xhr.addEventListener("abort", () => {
      reject(new DOMException("Aborted", "AbortError"));
    });

    const headers = getCopilotHeaders(token);
    xhr.open("POST", `${API_URL}/api/v1/copilot/media/upload`);
    // Set auth and tenant headers (not Content-Type — browser sets multipart boundary)
    Object.entries(headers).forEach(([key, val]) => {
      xhr.setRequestHeader(key, val);
    });

    xhr.send(fd);
  });
}

/** Infer media kind from MIME type */
export function inferMediaKind(mime: string): MediaKind {
  if (mime.startsWith("image/")) return "image";
  if (mime.startsWith("audio/")) return "audio";
  if (mime.startsWith("video/")) return "video";
  return "document";
}

/** Validate file MIME type against allowed types. Returns null if valid, error string if not. */
export function validateMimeType(file: File): string | null {
  const allowedMimes: Record<MediaKind, string[]> = {
    image: ["image/jpeg", "image/png", "image/webp", "image/gif", "image/svg+xml"],
    audio: ["audio/webm", "audio/mpeg", "audio/mp4", "audio/ogg", "audio/wav"],
    video: ["video/mp4", "video/webm", "video/quicktime"],
    document: [
      "application/pdf",
      "text/plain",
      "text/csv",
      "text/markdown",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      "application/vnd.openxmlformats-officedocument.presentationml.presentation",
      "application/msword",
      "application/vnd.ms-excel",
    ],
  };

  const all = Object.values(allowedMimes).flat();
  if (!all.includes(file.type)) {
    return `Tipo de archivo no soportado: ${file.name}`;
  }
  return null;
}

/** Size limits per kind in bytes */
const SIZE_LIMITS: Record<MediaKind, number> = {
  image: 10 * 1024 * 1024, // 10 MB
  audio: 25 * 1024 * 1024, // 25 MB
  video: 100 * 1024 * 1024, // 100 MB
  document: 20 * 1024 * 1024, // 20 MB
};

const SIZE_LABELS: Record<MediaKind, string> = {
  image: "10MB",
  audio: "25MB",
  video: "100MB",
  document: "20MB",
};

/** Validate file size. Returns null if valid, error string if not. */
export function validateFileSize(file: File, kind: MediaKind): string | null {
  const limit = SIZE_LIMITS[kind];
  if (file.size > limit) {
    return `El archivo ${file.name} supera el límite de ${SIZE_LABELS[kind]}.`;
  }
  return null;
}

/** Format bytes to human-readable string */
export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
