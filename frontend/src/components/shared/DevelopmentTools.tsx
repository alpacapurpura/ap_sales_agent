"use client";

import { ReactQueryDevtools } from "@tanstack/react-query-devtools";

export function DevelopmentTools() {
  // NODE_ENV is inlined at build time, so this is safe to check at render
  if (process.env.NODE_ENV !== "development") return null;

  return <ReactQueryDevtools initialIsOpen={false} buttonPosition="bottom-left" />;
}
