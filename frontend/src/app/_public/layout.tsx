import type { Metadata } from "next";

import { headers } from "next/headers";
import Script from "next/script";

import "@/app/globals.css";
import { getTrackingConfig } from "@/features/tenant-domains/utils/tracking";

export const metadata: Metadata = { title: "Nicolify" };

/** Allow only alphanumeric, hyphens, and dots — valid for GTM/GA4/Pixel IDs and URLs. */
function sanitizeTrackingId(value: string): string {
  return value.replace(/[^a-zA-Z0-9\-_.:/]/g, "");
}

/**
 *
 */
export default async function PublicSiteLayout({ children }: { children: React.ReactNode }) {
  const headersList = await headers();
  const tenantId = headersList.get("X-Tenant-ID") ?? "";
  const tracking = tenantId ? await getTrackingConfig(tenantId) : null;

  const gtmId = tracking?.gtm_container_id ? sanitizeTrackingId(tracking.gtm_container_id) : null;
  const gtmServerUrl = tracking?.gtm_server_url
    ? sanitizeTrackingId(tracking.gtm_server_url)
    : null;
  const pixelId = tracking?.meta_pixel_id ? sanitizeTrackingId(tracking.meta_pixel_id) : null;
  const gaMeasurementId = tracking?.ga_measurement_id
    ? sanitizeTrackingId(tracking.ga_measurement_id)
    : null;

  // GTM script URL — use server-side GTM if configured
  const gtmScriptSrc = gtmId
    ? gtmServerUrl
      ? `${gtmServerUrl}/gtm.js?id=${gtmId}`
      : `https://www.googletagmanager.com/gtm.js?id=${gtmId}`
    : null;

  return (
    <html lang="es">
      <head>
        {/* GTM */}
        {gtmId && gtmScriptSrc && (
          <Script
            id="gtm-init"
            strategy="afterInteractive"
            dangerouslySetInnerHTML={{
              __html: `(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src='${gtmScriptSrc}'+dl;f.parentNode.insertBefore(j,f);})(window,document,'script','dataLayer','${gtmId}');`,
            }}
          />
        )}

        {/* Meta Pixel */}
        {pixelId && (
          <Script
            id="meta-pixel-init"
            strategy="afterInteractive"
            dangerouslySetInnerHTML={{
              __html: `!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');fbq('init','${pixelId}');fbq('track','PageView');`,
            }}
          />
        )}

        {/* GA4 — only when GTM is not configured */}
        {gaMeasurementId && !gtmId && (
          <>
            <Script
              src={`https://www.googletagmanager.com/gtag/js?id=${gaMeasurementId}`}
              strategy="afterInteractive"
            />
            <Script
              id="ga4-init"
              strategy="afterInteractive"
              dangerouslySetInnerHTML={{
                __html: `window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments)}gtag('js',new Date());gtag('config','${gaMeasurementId}');`,
              }}
            />
          </>
        )}
      </head>
      <body className="antialiased">
        {/* GTM noscript fallback */}
        {gtmId && (
          <noscript>
            <iframe
              src={`https://www.googletagmanager.com/ns.html?id=${gtmId}`}
              height="0"
              width="0"
              style={{ display: "none", visibility: "hidden" }}
            />
          </noscript>
        )}
        {children}
      </body>
    </html>
  );
}
