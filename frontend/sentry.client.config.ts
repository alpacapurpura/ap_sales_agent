import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN || "",
  environment: process.env.NEXT_PUBLIC_ENVIRONMENT || "dev",
  tracesSampleRate: 0.1,
  replaysSessionSampleRate: 0,
  replaysOnErrorSampleRate: 0,
  sendDefaultPii: false,
  enabled: !!process.env.NEXT_PUBLIC_SENTRY_DSN,
  beforeBreadcrumb(breadcrumb) {
    if (breadcrumb.category === "fetch" || breadcrumb.category === "xhr") {
      delete breadcrumb.data?.headers;
    }
    return breadcrumb;
  },
});
