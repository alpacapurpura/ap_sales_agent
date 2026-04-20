import { NextResponse } from "next/server";

import type { NextRequest } from "next/server";

interface ExchangeResult {
  success: boolean;
  errorDetail: string;
}

async function exchangeShopifyToken(
  backendUrl: string,
  payload: Record<string, string>,
): Promise<ExchangeResult> {
  try {
    const response = await fetch(`${backendUrl}/api/v1/connections/shopify/auth/exchange`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const errorData = (await response.json().catch(() => ({}))) as { detail?: string };
      const errorDetail = errorData.detail || "Failed to exchange token";
      console.error("Shopify Exchange Error:", errorDetail);
      return { success: false, errorDetail };
    }
    return { success: true, errorDetail: "" };
  } catch (error: unknown) {
    console.error("Shopify Network Error:", error);
    return {
      success: false,
      errorDetail: error instanceof Error ? error.message : "Network error",
    };
  }
}

interface ShopifyAdminRedirectParams {
  shop: string;
  appId: string;
  host: string;
  success: boolean;
  errorDetail: string;
}

function buildShopifyAdminRedirect({
  shop,
  appId,
  host,
  success,
  errorDetail,
}: ShopifyAdminRedirectParams): URL {
  const shopName = shop.replace(".myshopify.com", "");
  const adminUrl = new URL(`https://admin.shopify.com/store/${shopName}/apps/${appId}`);
  adminUrl.searchParams.set("host", host);
  adminUrl.searchParams.set("shop", shop);
  adminUrl.searchParams.set("status", success ? "success" : "error");
  if (!success && errorDetail) {
    adminUrl.searchParams.set("message", errorDetail);
  }
  return adminUrl;
}

/**
 *
 */
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const code = searchParams.get("code");
  const hmac = searchParams.get("hmac");
  const shop = searchParams.get("shop");
  const state = searchParams.get("state");
  const host = searchParams.get("host");
  const timestamp = searchParams.get("timestamp");
  const appId = process.env.SHOPIFY_API_KEY;

  const connectionsPath = state ? `/${state}/connections/shopify` : "/";

  if (!code || !hmac || !shop) {
    return NextResponse.redirect(
      new URL(`${connectionsPath}?status=error&message=Missing required parameters`, request.url),
    );
  }

  if (!appId) {
    return NextResponse.redirect(
      new URL(
        `${connectionsPath}?status=error&message=Missing SHOPIFY_API_KEY configuration`,
        request.url,
      ),
    );
  }

  try {
    const backendUrl = process.env.INTERNAL_API_URL || "http://visionarias_brain_dev:8000";
    const payload: Record<string, string> = { code, hmac, shop };
    if (state) payload.state = state;
    if (host) payload.host = host;
    if (timestamp) payload.timestamp = timestamp;

    const { success: exchangeSuccess, errorDetail } = await exchangeShopifyToken(
      backendUrl,
      payload,
    );

    if (host) {
      return NextResponse.redirect(
        buildShopifyAdminRedirect({ shop, appId, host, success: exchangeSuccess, errorDetail }),
      );
    }

    const redirectUrl = new URL(connectionsPath, request.url);
    if (exchangeSuccess) {
      redirectUrl.searchParams.set("status", "success");
      redirectUrl.searchParams.set("channel", "shopify");
    } else {
      redirectUrl.searchParams.set("status", "error");
      redirectUrl.searchParams.set("message", errorDetail);
    }

    return NextResponse.redirect(redirectUrl);
  } catch (error: unknown) {
    console.error("Shopify Auth Fatal Error:", error);
    return NextResponse.redirect(
      new URL(
        `${connectionsPath}?status=error&message=${encodeURIComponent(error instanceof Error ? error.message : "Fatal error")}`,
        request.url,
      ),
    );
  }
}
