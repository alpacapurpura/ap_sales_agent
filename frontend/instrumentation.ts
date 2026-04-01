export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    await import("./sentry.server.config");
  }
}

export const onRequestError = async (
  error: unknown,
  request: { path: string; method: string },
  context: { routeType: string },
) => {
  const { captureRequestError } = await import("@sentry/nextjs");
  captureRequestError(error, request, context);
};
