import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN || "",
  environment: process.env.NEXT_PUBLIC_ENVIRONMENT || "dev",
  release: process.env.NEXT_PUBLIC_SENTRY_RELEASE,
  tracesSampleRate: 0.1,
  profilesSampleRate: 0.1,
  sendDefaultPii: false,
  enabled: !!process.env.NEXT_PUBLIC_SENTRY_DSN,
});
