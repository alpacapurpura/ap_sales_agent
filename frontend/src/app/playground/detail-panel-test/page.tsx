"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  DetailPanel,
  DetailPanelHeader,
  DetailPanelTitle,
  DetailPanelClose,
} from "@/components/ui/detail-panel";
import { Separator } from "@/components/ui/separator";
import { useCopilotStore } from "@/features/copilot/store/copilot-store";

/**
 * Playground page for testing DetailPanel positioning with CopilotPanel.
 * No auth required.
 */
export default function DetailPanelTestPage() {
  const [panelOpen, setPanelOpen] = useState(false);
  const { isOpen: copilotOpen, togglePanel } = useCopilotStore();

  return (
    <div className="min-h-screen bg-slate-50 p-8" style={{ paddingRight: copilotOpen ? 380 : 60 }}>
      <h1 className="text-2xl font-bold mb-4">DetailPanel Test</h1>
      <p className="text-sm text-muted-foreground mb-6">
        Validates that the DetailPanel sits to the LEFT of the copilot, never overlapping.
      </p>

      <div className="flex gap-3 mb-8">
        <Button data-testid="open-panel" onClick={() => setPanelOpen(true)}>
          Open DetailPanel
        </Button>
        <Button data-testid="toggle-copilot" variant="outline" onClick={togglePanel}>
          {copilotOpen ? "Collapse Copilot" : "Expand Copilot"}
        </Button>
      </div>

      <div className="text-sm space-y-1">
        <p>
          Copilot state:{" "}
          <strong data-testid="copilot-state">
            {copilotOpen ? "OPEN (380px)" : "COLLAPSED (60px rail)"}
          </strong>
        </p>
        <p>
          DetailPanel state:{" "}
          <strong data-testid="panel-state">{panelOpen ? "OPEN" : "CLOSED"}</strong>
        </p>
      </div>

      {/* Simulated copilot — same positioning as real CopilotPanel. Hidden on mobile like the real one. */}
      <div data-testid="mock-copilot" className="fixed right-0 top-0 z-40 hidden sm:flex h-screen">
        {copilotOpen ? (
          <div className="flex h-full w-[380px] flex-col border-l border-slate-200 bg-purple-600 text-white items-center justify-center">
            <p className="text-lg font-bold">Copilot Panel</p>
            <p className="text-sm opacity-75">380px - should stay visible</p>
          </div>
        ) : (
          <div className="flex h-full w-[60px] flex-col items-center border-l border-slate-200 bg-purple-700 py-4 text-white justify-center">
            <p className="text-xs writing-mode-vertical" style={{ writingMode: "vertical-lr" }}>
              Rail 60px
            </p>
          </div>
        )}
      </div>

      {/* The actual DetailPanel component */}
      <DetailPanel open={panelOpen} onClose={() => setPanelOpen(false)}>
        <DetailPanelHeader className="flex flex-row items-start justify-between pr-6">
          <div className="space-y-1">
            <DetailPanelTitle>Test Metric Detail</DetailPanelTitle>
            <p className="text-xs text-muted-foreground">
              This panel should NOT overlap the copilot
            </p>
          </div>
          <DetailPanelClose onClose={() => setPanelOpen(false)} className="flex-shrink-0" />
        </DetailPanelHeader>

        <div className="px-6">
          <Separator className="my-4" />
          <div className="space-y-4">
            <div className="space-y-1">
              <p className="text-xs uppercase tracking-widest text-muted-foreground font-medium">
                Valor actual
              </p>
              <span className="text-4xl font-bold tabular-nums">12,500</span>
            </div>
            <Separator />
            <p className="text-sm text-muted-foreground">
              If you can see the purple copilot panel to the right of this, the positioning is
              correct.
            </p>
          </div>
        </div>
      </DetailPanel>
    </div>
  );
}
