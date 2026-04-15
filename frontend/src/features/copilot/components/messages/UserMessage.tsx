"use client";

import { memo } from "react";

import type { CopilotMessage } from "../../store/copilot-store";

interface UserMessageProps {
  message: CopilotMessage;
}

export const UserMessage = memo(function UserMessage({ message }: UserMessageProps) {
  return (
    <div className="flex justify-end animate-in slide-in-from-bottom-2 fade-in duration-300">
      <div className="max-w-[85%] rounded-2xl rounded-br-sm bg-purple-600 px-4 py-2.5 text-sm text-white">
        {message.content}
      </div>
    </div>
  );
});
UserMessage.displayName = "UserMessage";
