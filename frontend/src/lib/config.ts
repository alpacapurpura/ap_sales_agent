export const config = {
  api: {
    // Default to localhost for development if not set
    baseUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  },
};
