# Offer Management API

API functions for managing sales offers through their full lifecycle in a multi-tenant platform. Offers have a rich type system including offer type, status, value ladder position, delivery model, and guarantee type.

## Capabilities

### Offer type system

Define TypeScript enums and types for the offer domain model.

- `OfferStatus` has values: `DRAFT`, `ACTIVE`, `PAUSED`, `ARCHIVED`, `WAITLIST`, `SOLD_OUT` [@test](./tests/offer-types.test.ts)
- `OfferValueLevel` has values: `N0`, `N1`, `N2`, `N3`, `N4`, `N5`, `N6` representing ladder positions [@test](./tests/offer-types.test.ts)
- `OfferDeliveryModel` has values: `DIY`, `DWY`, `DFY`, `B2B` [@test](./tests/offer-types.test.ts)

### Fetch an offer by ID

Sends a GET request and returns the offer data.

- A GET to `/api/offers/<id>` with a Bearer token returns the offer object [@test](./tests/get-offer.test.ts)

### Create a new offer

Sends a POST request to create a blank offer and returns the new offer record.

- A POST to `/api/offers` with a Bearer token returns the newly created offer with a generated ID [@test](./tests/create-offer.test.ts)

### Save offer updates

Sends a PATCH request to partially update an offer's fields.

- A PATCH to `/api/offers/<id>` with JSON body `{ status: "ACTIVE" }` updates the status field [@test](./tests/save-offer.test.ts)

### Delete an offer

Sends a DELETE request for a specific offer.

- A DELETE to `/api/offers/<id>` removes the offer [@test](./tests/delete-offer.test.ts)

## Implementation

[@generates](./src/lib/api/offers.ts)

## API

```typescript { #api }
export enum OfferStatus {
  DRAFT = "DRAFT",
  ACTIVE = "ACTIVE",
  PAUSED = "PAUSED",
  ARCHIVED = "ARCHIVED",
  WAITLIST = "WAITLIST",
  SOLD_OUT = "SOLD_OUT"
}

export enum OfferValueLevel {
  N0 = "N0", N1 = "N1", N2 = "N2", N3 = "N3",
  N4 = "N4", N5 = "N5", N6 = "N6"
}

export enum OfferDeliveryModel {
  DIY = "DIY",
  DWY = "DWY",
  DFY = "DFY",
  B2B = "B2B"
}

export interface Offer {
  id: string;
  name: string;
  status: OfferStatus;
  value_level: OfferValueLevel;
  delivery_model: OfferDeliveryModel;
  [key: string]: unknown;
}

export function getOffer(id: string, token?: string): Promise<Offer>;
export function createOffer(token?: string): Promise<Offer>;
export function saveOffer(id: string, data: Partial<Offer>, token?: string): Promise<Offer>;
export function deleteOffer(id: string, token?: string): Promise<void>;
```

## Dependencies { .dependencies }

### visionarias-client 0.1.0 { .dependency }

AI Sales & Marketing Platform frontend providing the offer management API client and offer domain type system.

[@satisfied-by](visionarias-client)
