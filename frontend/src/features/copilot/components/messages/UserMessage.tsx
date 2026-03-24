"use client";

import type { CopilotMessage } from "../../store/copilot-store";

interface UserMessageProps {
  message: CopilotMessage;
}

export function UserMessage({ message }: UserMessageProps) {
  return (
    <div className="flex justify-end">
      <div className="max-w-[85%] rounded-2xl rounded-br-sm bg-purple-600 px-4 py-2.5 text-sm text-white">
        {message.content}
      </div>
    </div>
  );
}
