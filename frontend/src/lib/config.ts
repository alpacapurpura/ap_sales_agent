export const config = {
  api: {
    // Server-side: use internal Docker URL (faster, no external hop)
    // Client-side: use public API URL; if empty, use relative path (same origin via rewrites)
    baseUrl: (typeof window === 'undefined' && process.env.INTERNAL_API_URL)
      ? process.env.INTERNAL_API_URL
      : (process.env.NEXT_PUBLIC_API_URL || ""),
  },
};
