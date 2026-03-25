"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { useCopilotStore } from "../store/copilot-store";
import { getCopilotHeaders } from "../api/copilot-api";
import { config } from "@/lib/config";

const API_URL = config.api.baseUrl;
const DISMISSED_KEY = "copilot:dismissed-nudges";

interface Nudge {
  id: string;
  type: string;
  module_id: string;
  title: string;
  message: string;
  suggested_prompt: string;
  priority: number;
}

function getDismissed(): Set<string> {
  try {
    const raw = localStorage.getItem(DISMISSED_KEY);
    return raw ? new Set(JSON.parse(raw)) : new Set();
  } catch {
    return new Set();
  }
}

function addDismissed(id: string) {
  const dismissed = getDismissed();
  dismissed.add(id);
  localStorage.setItem(DISMISSED_KEY, JSON.stringify([...dismissed]));
}

export function useProactiveNudges() {
  const { currentRoute } = useCopilotStore();
  const { getToken } = useAuth();
  const [nudges, setNudges] = useState<Nudge[]>([]);

  useEffect(() => {
    if (!currentRoute) return;

    let cancelled = false;

    async function fetchNudges() {
      try {
        const token = await getToken();
        if (!token || cancelled) return;

        const headers = getCopilotHeaders(token);

        const res = await fetch(
          `${API_URL}/api/v1/copilot/nudge-context?route=${encodeURIComponent(currentRoute || "")}`,
          { headers },
        );

        if (!res.ok || cancelled) return;

        const data = await res.json();
        const dismissed = getDismissed();
        const filtered = (data.nudges || []).filter(
          (n: Nudge) => !dismissed.has(n.id),
        );
        if (!cancelled) setNudges(filtered);
      } catch {
        // Nudges are best-effort
      }
    }

    fetchNudges();
    return () => { cancelled = true; };
  }, [currentRoute, getToken]);

  const dismissNudge = useCallback((id: string) => {
    addDismissed(id);
    setNudges((prev) => prev.filter((n) => n.id !== id));
  }, []);

  return { nudges, dismissNudge };
}
