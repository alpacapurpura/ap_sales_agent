"use client";

import { useAuth } from "@clerk/nextjs";
import { useCallback, useRef, useState } from "react";

import { transcribeAudio } from "../api/voice-api";

// ── Types ──────────────────────────────────────────────────────────────────

type RecorderState = "idle" | "recording" | "transcribing";

export interface UseVoiceRecorderReturn {
  isRecording: boolean;
  isTranscribing: boolean;
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<string>;
  cancelRecording: () => void;
  error: string | null;
  duration: number;
}

// ── Constants ──────────────────────────────────────────────────────────────

const PREFERRED_MIME_TYPES = [
  "audio/webm;codecs=opus",
  "audio/webm",
  "audio/mp4",
  "audio/ogg;codecs=opus",
];

const DURATION_INTERVAL_MS = 1000;

// ── Hook ───────────────────────────────────────────────────────────────────

/**
 *
 */
export function useVoiceRecorder(): UseVoiceRecorderReturn {
  const [state, setState] = useState<RecorderState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [duration, setDuration] = useState(0);

  const { getToken } = useAuth();

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  // Used by cancelRecording to prevent transcription after stop
  const cancelledRef = useRef(false);

  /** Stop all media tracks and clear the interval timer. */
  const cleanup = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (streamRef.current) {
      for (const track of streamRef.current.getTracks()) {
        track.stop();
      }
      streamRef.current = null;
    }
    mediaRecorderRef.current = null;
    chunksRef.current = [];
  }, []);

  /** Pick the first supported MIME type, falling back to browser default. */
  const getSupportedMimeType = useCallback((): string | undefined => {
    for (const mimeType of PREFERRED_MIME_TYPES) {
      if (MediaRecorder.isTypeSupported(mimeType)) {
        return mimeType;
      }
    }
    return undefined;
  }, []);

  // ── startRecording ─────────────────────────────────────────────────────

  const startRecording = useCallback(async () => {
    setError(null);
    setDuration(0);
    cancelledRef.current = false;
    chunksRef.current = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const mimeType = getSupportedMimeType();
      const recorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream);

      recorder.ondataavailable = (event: BlobEvent) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      recorder.onerror = () => {
        setError("Error durante la grabación.");
        cleanup();
        setState("idle");
      };

      mediaRecorderRef.current = recorder;
      recorder.start();
      setState("recording");

      // Duration counter
      timerRef.current = setInterval(() => {
        setDuration((prev) => prev + 1);
      }, DURATION_INTERVAL_MS);
    } catch {
      setError("No se pudo acceder al micrófono. Verifica los permisos.");
      setState("idle");
    }
  }, [cleanup, getSupportedMimeType]);

  // ── stopRecording ──────────────────────────────────────────────────────

  const stopRecording = useCallback(async (): Promise<string> => {
    const recorder = mediaRecorderRef.current;
    if (!recorder || recorder.state === "inactive") {
      return "";
    }

    // Stop the recorder — this fires ondataavailable + onstop
    return new Promise<string>((resolve) => {
      recorder.onstop = async () => {
        // Clear timer and tracks
        if (timerRef.current) {
          clearInterval(timerRef.current);
          timerRef.current = null;
        }
        if (streamRef.current) {
          for (const track of streamRef.current.getTracks()) {
            track.stop();
          }
          streamRef.current = null;
        }

        // If cancelled while stopping, don't transcribe
        if (cancelledRef.current) {
          setState("idle");
          chunksRef.current = [];
          mediaRecorderRef.current = null;
          resolve("");
          return;
        }

        const mimeType = recorder.mimeType || "audio/webm";
        const blob = new Blob(chunksRef.current, { type: mimeType });
        chunksRef.current = [];
        mediaRecorderRef.current = null;

        setState("transcribing");

        try {
          const token = await getToken();
          if (!token) {
            setError("No se pudo obtener el token de autenticación.");
            setState("idle");
            resolve("");
            return;
          }

          const result = await transcribeAudio(blob, token);
          setError(null);
          setState("idle");
          resolve(result.text);
        } catch {
          setError("Error al transcribir el audio. Intenta de nuevo.");
          setState("idle");
          resolve("");
        }
      };

      recorder.stop();
    });
  }, [getToken]);

  // ── cancelRecording ────────────────────────────────────────────────────

  const cancelRecording = useCallback(() => {
    cancelledRef.current = true;
    const recorder = mediaRecorderRef.current;
    if (recorder && recorder.state !== "inactive") {
      recorder.stop();
    }
    cleanup();
    setState("idle");
    setDuration(0);
  }, [cleanup]);

  // ── Return ─────────────────────────────────────────────────────────────

  return {
    isRecording: state === "recording",
    isTranscribing: state === "transcribing",
    startRecording,
    stopRecording,
    cancelRecording,
    error,
    duration,
  };
}
