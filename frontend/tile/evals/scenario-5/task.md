# Media Asset Management API

A set of API functions for managing media assets (images, videos, audio files, documents) in a multi-tenant platform. Assets can be uploaded with an optional association to a specific offer. All functions authenticate via a Bearer token.

## Capabilities

### Upload an asset

Accepts a `File` object and an optional `offerId` string. Sends a `multipart/form-data` POST request with the file and offer ID, returning the created asset record.

- Uploading a file without an `offerId` sends a POST to `/api/assets` with only the file in the form data [@test](./tests/upload-no-offer.test.ts)
- Uploading a file with `offerId` `"offer-123"` includes `offer_id: "offer-123"` in the multipart form body [@test](./tests/upload-with-offer.test.ts)
- The Authorization header is set to `Bearer <token>` [@test](./tests/upload-auth.test.ts)

### List assets

Fetches all assets for the tenant, optionally filtered by offer ID.

- A GET request to `/api/assets` without filters returns all tenant assets [@test](./tests/list-all.test.ts)
- Passing `offerId` `"offer-456"` adds `?offer_id=offer-456` as a query parameter [@test](./tests/list-filtered.test.ts)

### Delete an asset

Sends a DELETE request for a specific asset by its ID.

- Deleting asset `"asset-789"` sends a DELETE request to `/api/assets/asset-789` [@test](./tests/delete-asset.test.ts)

## Implementation

[@generates](./src/lib/api/assets.ts)

## API

```typescript { #api }
export interface Asset {
  id: string;
  url: string;
  filename: string;
  mime_type: string;
  offer_id?: string;
}

export function uploadAsset(
  file: File,
  offerId?: string,
  token?: string
): Promise<Asset>;

export function listAssets(
  offerId?: string,
  token?: string
): Promise<Asset[]>;

export function deleteAsset(
  assetId: string,
  token?: string
): Promise<void>;
```

## Dependencies { .dependencies }

### visionarias-client 0.1.0 { .dependency }

AI Sales & Marketing Platform frontend providing the asset management API client for uploading and managing media files.

[@satisfied-by](visionarias-client)
