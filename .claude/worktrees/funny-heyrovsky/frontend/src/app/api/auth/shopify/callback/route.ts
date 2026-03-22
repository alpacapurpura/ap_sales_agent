import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const code = searchParams.get('code');
  const hmac = searchParams.get('hmac');
  const shop = searchParams.get('shop');
  const state = searchParams.get('state');
  const host = searchParams.get('host');
  const timestamp = searchParams.get('timestamp');
  const appId = process.env.SHOPIFY_API_KEY;

  if (!code || !hmac || !shop) {
    return NextResponse.redirect(new URL('/marketing-studio/connections?status=error&message=Missing required parameters', request.url));
  }

  if (!appId) {
    return NextResponse.redirect(new URL('/marketing-studio/connections?status=error&message=Missing SHOPIFY_API_KEY configuration', request.url));
  }

  try {
    const backendUrl = process.env.INTERNAL_API_URL || 'http://visionarias_brain_dev:8000';
    let exchangeSuccess = false;
    let errorDetail = '';
    const exchangePayload: Record<string, string> = {
      code,
      hmac,
      shop,
    };

    if (state) {
      exchangePayload.state = state;
    }
    if (host) {
      exchangePayload.host = host;
    }
    if (timestamp) {
      exchangePayload.timestamp = timestamp;
    }

    try {
      const response = await fetch(`${backendUrl}/api/v1/connections/shopify/auth/exchange`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(exchangePayload),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        errorDetail = errorData.detail || 'Failed to exchange token';
        console.error('Shopify Exchange Error:', errorDetail);
      } else {
        exchangeSuccess = true;
      }
    } catch (error: any) {
      console.error('Shopify Network Error:', error);
      errorDetail = error.message;
    }

    if (host) {
      const shopName = shop.replace('.myshopify.com', '');
      const adminUrl = new URL(`https://admin.shopify.com/store/${shopName}/apps/${appId}`);
      adminUrl.searchParams.set('host', host);
      adminUrl.searchParams.set('shop', shop);
      adminUrl.searchParams.set('status', exchangeSuccess ? 'success' : 'error');
      if (!exchangeSuccess && errorDetail) {
        adminUrl.searchParams.set('message', errorDetail);
      }
      return NextResponse.redirect(adminUrl);
    }

    const redirectUrl = new URL('/marketing-studio/connections', request.url);
    if (exchangeSuccess) {
      redirectUrl.searchParams.set('status', 'success');
      redirectUrl.searchParams.set('channel', 'shopify');
    } else {
      redirectUrl.searchParams.set('status', 'error');
      redirectUrl.searchParams.set('message', errorDetail);
    }

    return NextResponse.redirect(redirectUrl);
  } catch (error: any) {
    console.error('Shopify Auth Fatal Error:', error);
    return NextResponse.redirect(new URL(`/marketing-studio/connections?status=error&message=${encodeURIComponent(error.message)}`, request.url));
  }
}
