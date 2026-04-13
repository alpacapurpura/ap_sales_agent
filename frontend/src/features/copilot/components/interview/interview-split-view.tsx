"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";

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
import { getPreview } from "@/features/copilot/config/interview-preview-registry";

import { InterviewHeader } from "./interview-header";
import { SessionRestoreModal } from "./session-restore-modal";

// ── Props ────────────────────────────────────────────────────────────────────

interface InterviewSplitViewProps {
  /** The interview domain (e.g. "brand", "buyer_persona", "offer") */
  domain: string;
  /** Session ID from URL query param. If undefined, we detect or create one. */
  sessionId?: string;
  /** Entity ID for domain-specific interviews (e.g. offerId, personaId) */
  entityId?: string;
  /** Base route for URL updates (e.g. "brand-studio/interview") */
  routeBase?: string;
}

// ── Component ────────────────────────────────────────────────────────────────

export function InterviewSplitView({
  domain,
  sessionId: sessionIdProp,
  entityId,
  routeBase,
}: InterviewSplitViewProps) {
  const router = useRouter();
  const params = useParams();
  const tenantId = params.tenantId as string;
  const queryClient = useQueryClient();
  const { getToken } = useAuth();

  // Resolve the preview config from the registry
  const preview = getPreview(domain);
  const PreviewSummary = preview.summaryComponent;
  const PreviewSections = preview.sectionsComponent;

  // Active session ID (from URL or discovered)
  const [sessionId, setSessionId] = useState<string | null>(sessionIdProp ?? null);
  const [conversationId, setConversationId] = useState<string | null>(null);

  // Session restore modal state
  const [showRestoreModal, setShowRestoreModal] = useState(false);
  const [activeInterview, setActiveInterview] = useState<ActiveInterviewResponse | null>(null);
  const [isStarting, setIsStarting] = useState(false);

  // Interview preview data from copilot store (draft values from mapa_global)
  const { interviewPreviewData, setInterviewMode, updateInterviewPreview } = useCopilotStore();

  // ── Interview chat hook ──────────────────────────────────────────────────

  const { messages, status, sendMessage, sendCardAction, addInitialMessage } =
    useInterviewChat(sessionId, conversationId);

  // ── Detect active session on mount (when no sessionId in URL) ──────────

  const { data: activeInterviewData, isLoading: isCheckingActive } = useQuery({
    queryKey: ["interview-active", domain],
    queryFn: async () => {
      const token = await getToken();
      if (!token) return null;
      return getActiveInterview(token);
    },
    enabled: !sessionIdProp,
    staleTime: 0,
    retry: false,
  });

  // Load interview state when sessionId is available
  const { data: interviewState, isLoading: isLoadingState } = useQuery({
    queryKey: ["interview-state", sessionId],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No auth token");
      return getInterviewState(token, sessionId!);
    },
    enabled: !!sessionId,
    staleTime: 0,
    retry: false,
  });

  // ── Resolve route base for URL updates ─────────────────────────────────

  const resolvedRouteBase = routeBase ?? `${domain.replace("_", "-")}-studio/interview`;

  // ── Handle active interview detection ───────────────────────────────────

  useEffect(() => {
    if (sessionIdProp || isCheckingActive) return;

    if (activeInterviewData) {
      setActiveInterview(activeInterviewData);
      setShowRestoreModal(true);
    } else {
      handleStartNewSession();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeInterviewData, isCheckingActive, sessionIdProp]);

  // ── When sessionId is set, sync interview mode in store ─────────────────

  useEffect(() => {
    if (sessionId) {
      setInterviewMode(true, sessionId);
    }
  }, [sessionId, setInterviewMode]);

  // ── When interview state loads, populate preview data ───────────────────

  useEffect(() => {
    if (!interviewState) return;

    if (
      interviewState.mapa_global &&
      Object.keys(interviewState.mapa_global).length > 0
    ) {
      updateInterviewPreview(interviewState.mapa_global);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [interviewState]);

  // ── Session management ───────────────────────────────────────────────────

  const handleStartNewSession = useCallback(async () => {
    setIsStarting(true);
    try {
      const token = await getToken();
      if (!token) throw new Error("No auth token");
      const response = await startInterview(token, domain);
      setSessionId(response.session_id);
      setConversationId(response.conversation_id);
      router.replace(
        `/${tenantId}/${resolvedRouteBase}?session=${response.session_id}`,
      );
      if (response.initial_message) {
        addInitialMessage(response.initial_message);
      }
      await queryClient.invalidateQueries({ queryKey: ["interview-active", domain] });
    } catch (err) {
      console.error("Error starting interview:", err);
    } finally {
      setIsStarting(false);
    }
  }, [domain, tenantId, resolvedRouteBase, router, addInitialMessage, queryClient, getToken]);

  const handleContinueSession = useCallback(() => {
    if (!activeInterview) return;
    setShowRestoreModal(false);
    setSessionId(activeInterview.session_id);
    router.replace(
      `/${tenantId}/${resolvedRouteBase}?session=${activeInterview.session_id}`,
    );
  }, [activeInterview, tenantId, resolvedRouteBase, router]);

  const handleStartOver = useCallback(async () => {
    setIsStarting(true);
    try {
      if (activeInterview) {
        const token = await getToken();
        if (token) await abandonInterview(token, activeInterview.session_id);
      }
      setShowRestoreModal(false);
      await handleStartNewSession();
    } catch (err) {
      console.error("Error abandoning session:", err);
      setIsStarting(false);
    }
  }, [activeInterview, handleStartNewSession, getToken]);

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
  const currentBlock =
    interviewState?.bloque_actual ?? activeInterview?.bloque_actual ?? "";
  const blocksCompleted =
    interviewState?.bloques_completados?.length ??
    activeInterview?.bloques_completados?.length ??
    0;
  const blocksCompletedList =
    interviewState?.bloques_completados ??
    activeInterview?.bloques_completados ??
    [];
  const displayTotalBlocks =
    activeInterview?.total_bloques ??
    (interviewState?.config?.total_bloques as number | undefined) ??
    5;

  // Preview data for registry components
  const previewData: Record<string, unknown> = {
    ...(interviewPreviewData ?? {}),
    currentBlock,
    entityId,
  };

  // ── Render ───────────────────────────────────────────────────────────────

  return (
    <>
      {/* Session restore modal */}
      <SessionRestoreModal
        open={showRestoreModal}
        blocksCompleted={activeInterview?.bloques_completados?.length ?? 0}
        totalBlocks={activeInterview?.total_bloques ?? 5}
        onContinue={handleContinueSession}
        onStartOver={handleStartOver}
        isLoading={isStarting}
      />

      {/* Interview Header */}
      <InterviewHeader
        currentBlockLabel={currentBlock}
        blocksCompleted={blocksCompleted}
        totalBlocks={displayTotalBlocks}
      />

      {/* Split layout */}
      <div className="flex h-[calc(100vh-7.5rem)] overflow-hidden">
        {/* Left panel: Domain-specific preview */}
        <div className="hidden lg:flex flex-col w-1/2 border-r border-white/10 overflow-hidden bg-background">
          {/* Summary from registry */}
          <PreviewSummary
            data={previewData}
            completenessScore={0}
          />

          {/* Sections from registry */}
          <PreviewSections
            data={previewData}
            currentBlock={currentBlock}
            blocksCompleted={blocksCompletedList}
          />
        </div>

        {/* Right panel: Interview chat */}
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
