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
  /** Normalized 0..1 audio level, updated ~60Hz while recording. Drops to 0 when idle/transcribing. */
  audioLevel: number;
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
  const [audioLevel, setAudioLevel] = useState(0);

  const { getToken } = useAuth();

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  // Used by cancelRecording to prevent transcription after stop
  const cancelledRef = useRef(false);
  // Audio level analysis
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const rafRef = useRef<number | null>(null);

  /** Stop all media tracks and clear the interval timer. */
  const cleanup = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (rafRef.current !== null) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
    if (analyserRef.current) {
      analyserRef.current.disconnect();
      analyserRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== "closed") {
      audioContextRef.current.close().catch(() => {
        /* ignore */
      });
      audioContextRef.current = null;
    }
    if (streamRef.current) {
      for (const track of streamRef.current.getTracks()) {
        track.stop();
      }
      streamRef.current = null;
    }
    mediaRecorderRef.current = null;
    chunksRef.current = [];
    setAudioLevel(0);
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

      // Audio level analyser — feeds VoiceWaveform visualization
      try {
        const AudioCtx =
          window.AudioContext ??
          (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
        if (AudioCtx) {
          const ctx = new AudioCtx();
          audioContextRef.current = ctx;
          const source = ctx.createMediaStreamSource(stream);
          const analyser = ctx.createAnalyser();
          analyser.fftSize = 1024;
          analyser.smoothingTimeConstant = 0.6;
          source.connect(analyser);
          analyserRef.current = analyser;

          const buffer = new Uint8Array(analyser.frequencyBinCount);
          const tick = () => {
            if (!analyserRef.current) return;
            analyserRef.current.getByteTimeDomainData(buffer);
            // Peak deviation from 128 (silence midpoint) → normalized 0..1
            let peak = 0;
            for (const sample of buffer) {
              const v = Math.abs(sample - 128);
              if (v > peak) peak = v;
            }
            setAudioLevel(Math.min(1, peak / 128));
            rafRef.current = requestAnimationFrame(tick);
          };
          rafRef.current = requestAnimationFrame(tick);
        }
      } catch {
        // Analyser is decorative — recording still works without it
      }

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
        // Clear timer, analyser, and tracks
        if (timerRef.current) {
          clearInterval(timerRef.current);
          timerRef.current = null;
        }
        if (rafRef.current !== null) {
          cancelAnimationFrame(rafRef.current);
          rafRef.current = null;
        }
        if (analyserRef.current) {
          analyserRef.current.disconnect();
          analyserRef.current = null;
        }
        if (audioContextRef.current && audioContextRef.current.state !== "closed") {
          audioContextRef.current.close().catch(() => {
            /* ignore */
          });
          audioContextRef.current = null;
        }
        setAudioLevel(0);
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
    audioLevel,
  };
}
