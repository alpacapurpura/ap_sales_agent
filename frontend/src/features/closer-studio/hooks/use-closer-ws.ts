"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useCallback } from "react";

import { useCloserStore } from "../store/closer-store";

interface WSEvent {
  type: string;
  lead_id?: string;
  role?: string;
  content?: string;
  handler_mode?: string;
  lead_score?: number;
  funnel_stage?: string;
  [key: string]: unknown;
}

const MAX_RETRIES = 10;
const BASE_DELAY = 1000; // 1s

/**
 *
 */
export function useCloserWebSocket(tenantId: string | null) {
  const wsRef = useRef<WebSocket | null>(null);
  const retriesRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const qc = useQueryClient();
  const setWsConnected = useCloserStore((s) => s.setWsConnected);
  const incrementUnread = useCloserStore((s) => s.incrementUnread);
  const selectedLeadId = useCloserStore((s) => s.selectedLeadId);

  const handleEvent = useCallback(
    (event: WSEvent) => {
      switch (event.type) {
        case "new_message":
          // Invalidate conversation list + detail
          void qc.invalidateQueries({ queryKey: ["closer-studio", "conversations"] });
          if (event.lead_id) {
            void qc.invalidateQueries({
              queryKey: ["closer-studio", "detail", event.lead_id],
            });
            // Increment unread if not currently viewing
            if (event.lead_id !== selectedLeadId && event.role === "user") {
              incrementUnread(event.lead_id);
            }
          }
          break;

        case "handler_changed":
        case "conversation_updated":
          void qc.invalidateQueries({ queryKey: ["closer-studio"] });
          break;

        default:
          break;
      }
    },
    [qc, selectedLeadId, incrementUnread],
  );

  const connectRef = useRef<(() => void) | undefined>(undefined);

  const connect = useCallback(() => {
    if (!tenantId) return;

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = process.env.NEXT_PUBLIC_API_URL
      ? new URL(process.env.NEXT_PUBLIC_API_URL).host
      : window.location.host;
    const url = `${protocol}//${host}/ws/closer-studio?tenant_id=${tenantId}`;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setWsConnected(true);
      retriesRef.current = 0;
    };

    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data as string) as WSEvent;
        if (data.type) handleEvent(data);
      } catch {
        // Ignore non-JSON (e.g., "pong")
      }
    };

    ws.onclose = () => {
      setWsConnected(false);
      wsRef.current = null;

      // Exponential backoff reconnect
      if (retriesRef.current < MAX_RETRIES) {
        const delay = BASE_DELAY * Math.pow(2, retriesRef.current);
        retriesRef.current++;
        timerRef.current = setTimeout(() => connectRef.current?.(), delay);
      }
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [tenantId, handleEvent, setWsConnected]);

  useEffect(() => {
    connectRef.current = connect;
    connect();

    // Keep-alive ping every 30s
    const pingInterval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send("ping");
      }
    }, 30_000);

    return () => {
      clearInterval(pingInterval);
      if (timerRef.current) clearTimeout(timerRef.current);
      if (wsRef.current) {
        wsRef.current.onclose = null; // Prevent reconnect on intentional close
        wsRef.current.close();
      }
      setWsConnected(false);
    };
  }, [connect, setWsConnected]);
}
