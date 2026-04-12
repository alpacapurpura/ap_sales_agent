"use client";

import { useEffect, useState, useMemo, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { Loader2 } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";

import {
  getActiveInterview,
  getInterviewState,
  startInterview,
  abandonInterview,
  type ActiveInterviewResponse,
} from "@/features/copilot/api/interview-api";
import { useCopilotStore } from "@/features/copilot/store/copilot-store";
import { useInterviewChat } from "@/features/copilot/hooks/useInterviewChat";
import { InterviewChatPanel } from "@/features/copilot/components/interview/interview-chat-panel";

import { useBrandSettings } from "@/features/brand/hooks/useBrandSettings";
import { BrandStudioTabs } from "@/features/brand/components/tabs/brand-studio-tabs";
import type { BrandSectionId } from "@/features/brand/config/sections";
import type { BrandSettings } from "@/features/brand/types";

import { InterviewHeader } from "./interview-header";
import { SessionRestoreModal } from "./session-restore-modal";

// ── Section views (consume BrandStudioContext from parent layout) ────────────
import { EsenciaView } from "@/features/brand/components/views/esencia-view";
import { EstrategiaView } from "@/features/brand/components/views/estrategia-view";
import { PublicoView } from "@/features/brand/components/views/publico-view";
import { IdentidadCreativaView } from "@/features/brand/components/views/identidad-creativa-view";

// ── Block → Tab mapping ──────────────────────────────────────────────────────

const BLOCK_TO_TAB: Record<string, BrandSectionId> = {
  identidad: "esencia",
  posicionamiento: "estrategia",
  narrativa: "estrategia",
  publico: "publico",
  identidad_creativa: "identidad-creativa",
};

// ── Section view renderer ────────────────────────────────────────────────────

function PreviewSection({ activeTab }: { activeTab: BrandSectionId }) {
  switch (activeTab) {
    case "esencia":
      return <EsenciaView />;
    case "estrategia":
      return <EstrategiaView />;
    case "publico":
      return <PublicoView />;
    case "identidad-creativa":
      return <IdentidadCreativaView />;
    default:
      return <EsenciaView />;
  }
}

// ── Props ────────────────────────────────────────────────────────────────────

interface InterviewSplitViewProps {
  /** Session ID from ?session= query param. If undefined, we detect or create one. */
  sessionId?: string;
}

// ── Component ────────────────────────────────────────────────────────────────

export function InterviewSplitView({ sessionId: sessionIdProp }: InterviewSplitViewProps) {
  const router = useRouter();
  const params = useParams();
  const tenantId = params.tenantId as string;
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  // Active session ID (from URL or discovered)
  const [sessionId, setSessionId] = useState<string | null>(sessionIdProp ?? null);
  const [conversationId, setConversationId] = useState<string | null>(null);

  // Tab shown in the left panel
  const [activeTab, setActiveTab] = useState<BrandSectionId>("esencia");

  // Session restore modal state
  const [showRestoreModal, setShowRestoreModal] = useState(false);
  const [activeInterview, setActiveInterview] = useState<ActiveInterviewResponse | null>(null);
  const [isStarting, setIsStarting] = useState(false);

  // Brand settings (live data from cache)
  const { settings } = useBrandSettings();

  // Interview preview data from copilot store (draft values from mapa_global)
  const { interviewPreviewData, setInterviewMode, updateInterviewPreview } = useCopilotStore();

  // Merged preview settings: live settings + interview draft overlay
  const mergedSettings = useMemo<BrandSettings | null>(() => {
    if (!settings) return null;
    if (!interviewPreviewData) return settings;
    // Shallow-merge top-level keys from mapa_global into settings
    return {
      ...settings,
      ...Object.fromEntries(
        Object.entries(interviewPreviewData).map(([k, v]) => [
          k,
          typeof v === "object" && v !== null && !Array.isArray(v)
            ? { ...(settings[k as keyof BrandSettings] as object ?? {}), ...(v as object) }
            : v,
        ]),
      ),
    } as BrandSettings;
  }, [settings, interviewPreviewData]);

  // ── Interview chat hook ──────────────────────────────────────────────────

  const { messages, status, sendMessage, sendCardAction, addInitialMessage } =
    useInterviewChat(sessionId, conversationId);

  // ── Detect active session on mount (when no sessionId in URL) ──────────

  const { data: activeInterviewData, isLoading: isCheckingActive } = useQuery({
    queryKey: ["interview-active"],
    queryFn: getActiveInterview,
    enabled: !sessionIdProp, // Only when no session in URL
    staleTime: 0,
    retry: false,
  });

  // Load interview state when sessionId is available
  const { data: interviewState, isLoading: isLoadingState } = useQuery({
    queryKey: ["interview-state", sessionId],
    queryFn: () => getInterviewState(sessionId!),
    enabled: !!sessionId,
    staleTime: 0,
    retry: false,
  });

  // ── Handle active interview detection ───────────────────────────────────

  useEffect(() => {
    if (sessionIdProp || isCheckingActive) return;

    if (activeInterviewData) {
      // Found an active session — show the restore modal
      setActiveInterview(activeInterviewData);
      setShowRestoreModal(true);
    } else {
      // No active session — start a new one immediately
      handleStartNewSession();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeInterviewData, isCheckingActive, sessionIdProp]);

  // ── When sessionId is set, sync interview mode in store ─────────────────

  useEffect(() => {
    if (sessionId) {
      setInterviewMode(true, sessionId);
    }
    return () => {
      // Only clear on unmount if session is active
    };
  }, [sessionId, setInterviewMode]);

  // ── When interview state loads, populate preview data + initial message ─

  useEffect(() => {
    if (!interviewState) return;

    // Hydrate copilot store preview data from mapa_global
    if (
      interviewState.mapa_global &&
      Object.keys(interviewState.mapa_global).length > 0
    ) {
      updateInterviewPreview(interviewState.mapa_global);
    }

    // Update active tab based on current block
    const block = interviewState.bloque_actual;
    const tab = BLOCK_TO_TAB[block];
    if (tab) {
      setActiveTab(tab);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [interviewState]);

  // ── Auto-switch tab when block changes (via messages) ───────────────────

  // Track current block from copilot store (updated via preview_update actions)
  // We use the interviewState.bloque_actual as initial sync, and messages for live updates.

  // ── Session management ───────────────────────────────────────────────────

  const handleStartNewSession = useCallback(async () => {
    setIsStarting(true);
    try {
      const response = await startInterview("brand");
      setSessionId(response.session_id);
      setConversationId(response.conversation_id);
      // Redirect to add ?session= param to URL so refreshes restore the session
      router.replace(`/${tenantId}/brand-studio/interview?session=${response.session_id}`);
      // Show initial message from the interview
      if (response.initial_message) {
        addInitialMessage(response.initial_message);
      }
      // Invalidate active interview check
      await queryClient.invalidateQueries({ queryKey: ["interview-active"] });
    } catch (err) {
      console.error("Error starting interview:", err);
    } finally {
      setIsStarting(false);
    }
  }, [tenantId, router, addInitialMessage, queryClient]);

  const handleContinueSession = useCallback(() => {
    if (!activeInterview) return;
    setShowRestoreModal(false);
    setSessionId(activeInterview.session_id);
    router.replace(
      `/${tenantId}/brand-studio/interview?session=${activeInterview.session_id}`,
    );
  }, [activeInterview, tenantId, router]);

  const handleStartOver = useCallback(async () => {
    setIsStarting(true);
    try {
      if (activeInterview) {
        await abandonInterview(activeInterview.session_id);
      }
      setShowRestoreModal(false);
      await handleStartNewSession();
    } catch (err) {
      console.error("Error abandoning session:", err);
      setIsStarting(false);
    }
  }, [activeInterview, handleStartNewSession]);

  // ── Loading state ────────────────────────────────────────────────────────

  const isLoading = isCheckingActive || isLoadingState || isStarting;

  if (isLoading && !sessionId && !showRestoreModal) {
    return (
      <div className="flex h-[calc(100vh-6rem)] items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-purple-400" />
      </div>
    );
  }

  // Determine current block info
  const currentBlock = interviewState?.bloque_actual ?? activeInterview?.bloque_actual ?? "";
  const blocksCompleted =
    interviewState?.bloques_completados?.length ??
    activeInterview?.bloques_completados?.length ??
    0;
  const totalBlocks =
    interviewState
      ? (interviewState.bloques_completados.length +
          (interviewState.bloque_actual ? 1 : 0))
      : (activeInterview?.total_bloques ?? 5);

  const displayTotalBlocks = activeInterview?.total_bloques ?? interviewState?.config?.total_bloques as number | undefined ?? 5;

  // ── Render ───────────────────────────────────────────────────────────────

  return (
    <>
      {/* Session restore modal — shown when active session detected without URL param */}
      <SessionRestoreModal
        open={showRestoreModal}
        blocksCompleted={activeInterview?.bloques_completados?.length ?? 0}
        totalBlocks={activeInterview?.total_bloques ?? 5}
        onContinue={handleContinueSession}
        onStartOver={handleStartOver}
        isLoading={isStarting}
      />

      {/* Interview Header — spans full width above the split */}
      <InterviewHeader
        currentBlockLabel={currentBlock}
        blocksCompleted={blocksCompleted}
        totalBlocks={displayTotalBlocks}
      />

      {/* Split layout */}
      <div className="flex h-[calc(100vh-7.5rem)] overflow-hidden">
        {/* ── Left panel: Brand preview ─────────────────────────────────── */}
        <div className="hidden lg:flex flex-col w-1/2 border-r border-white/10 overflow-hidden bg-background">
          {/* Tab bar for switching preview sections */}
          {mergedSettings && (
            <BrandStudioTabs
              activeTab={activeTab}
              onTabChange={setActiveTab}
              settings={mergedSettings}
            />
          )}

          {/* Section preview */}
          <div className="flex-1 overflow-hidden">
            <ScrollArea className="h-full">
              <PreviewSection activeTab={activeTab} />
            </ScrollArea>
          </div>
        </div>

        {/* ── Right panel: Interview chat ───────────────────────────────── */}
        <div className="flex flex-col flex-1 overflow-hidden">
          <InterviewChatPanel
            messages={messages}
            status={status}
            onSend={sendMessage}
            onCardAction={sendCardAction}
          />
        </div>
      </div>
    </>
  );
}
