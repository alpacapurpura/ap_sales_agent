import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const code = searchParams.get('code');
  const hmac = searchParams.get('hmac');
  const shop = searchParams.get('shop');
  const state = searchParams.get('state');
  const host = searchParams.get('host');
  const timestamp = searchParams.get('timestamp');

  if (!code || !hmac || !shop || !state) {
    return NextResponse.redirect(new URL('/marketing-studio/connections?status=error&message=Missing required parameters', request.url));
  }

  try {
    // Use INTERNAL_API_URL for server-to-server communication within Docker network
    const backendUrl = process.env.INTERNAL_API_URL || 'http://visionarias_brain_dev:8000';
    
    const response = await fetch(`${backendUrl}/api/v1/connections/shopify/auth/exchange`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        code,
        hmac,
        shop,
        state,
        host,
        timestamp
      }),
    });

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to exchange token');
    }

    // Success: Redirect to connections page with success status
    // Include host param if available for App Bridge context
    const redirectUrl = new URL('/marketing-studio/connections', request.url);
    redirectUrl.searchParams.set('status', 'success');
    redirectUrl.searchParams.set('channel', 'shopify');
    if (host) {
      redirectUrl.searchParams.set('host', host);
    }
    
    return NextResponse.redirect(redirectUrl);

  } catch (error: any) {
    console.error('Shopify Auth Error:', error);
    return NextResponse.redirect(new URL(`/marketing-studio/connections?status=error&message=${encodeURIComponent(error.message)}`, request.url));
  }
}
