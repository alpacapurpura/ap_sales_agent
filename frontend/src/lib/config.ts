export const config = {
  api: {
    // Select URL based on environment (Server vs Client)
    // Server: Use internal Docker network (faster, secure)
    // Client: Use configured public/local URL. If empty, use relative path (same origin).
    baseUrl: (typeof window === 'undefined' && process.env.INTERNAL_API_URL)
      ? process.env.INTERNAL_API_URL
      : (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"),
  },
};
