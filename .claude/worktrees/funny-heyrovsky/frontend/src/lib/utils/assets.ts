import { config } from "../config";

const API_URL = config.api.baseUrl;

/**
 * Resolves an asset public_url to a fully-qualified URL.
 *
 * - If the URL is already absolute (starts with http/https), returns it as-is.
 *   This covers assets stored in Cloudflare R2 (https://assets.nicolify.com/...)
 * - If the URL is relative (/static/uploads/...), prepends the API base URL.
 *   This maintains backward compatibility with locally-stored assets.
 */
export function getAssetUrl(publicUrl?: string | null): string {
  if (!publicUrl) return "";
  if (publicUrl.startsWith("http://") || publicUrl.startsWith("https://")) {
    return publicUrl;
  }
  return `${API_URL}${publicUrl}`;
}
