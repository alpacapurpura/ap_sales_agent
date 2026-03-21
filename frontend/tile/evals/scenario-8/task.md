# Scheduling Event Types API

API functions for managing schedulable event types in a booking system. Event types define the rules for how appointments can be booked — including duration, availability, scheduling limits, and buffer times.

## Capabilities

### List event types

Fetches all event types for the authenticated tenant.

- A GET request to `/api/event-types` with a Bearer token returns an array of event type objects [@test](./tests/list-event-types.test.ts)

### Create an event type

Sends a POST request to create a new event type with the provided configuration.

- A POST to `/api/event-types` with a JSON body containing `{ name: "30-min Call", duration: 30 }` creates a new event type and returns the created record [@test](./tests/create-event-type.test.ts)
- The request includes `Content-Type: application/json` and `Authorization: Bearer <token>` [@test](./tests/create-event-type-headers.test.ts)

### Update an event type

Sends a PATCH request to partially update an existing event type by ID.

- A PATCH to `/api/event-types/<id>` with `{ duration: 60 }` updates only the duration field [@test](./tests/update-event-type.test.ts)

### Delete an event type

Sends a DELETE request to remove an event type by ID.

- A DELETE to `/api/event-types/<id>` removes the event type [@test](./tests/delete-event-type.test.ts)

## Implementation

[@generates](./src/lib/api/event-types.ts)

## API

```typescript { #api }
export interface EventType {
  id: string;
  name: string;
  duration: number;
  max_per_day?: number;
  max_per_week?: number;
  buffer_before?: number;
  buffer_after?: number;
  [key: string]: unknown;
}

export function listEventTypes(token?: string): Promise<EventType[]>;
export function createEventType(data: Partial<EventType>, token?: string): Promise<EventType>;
export function updateEventType(id: string, data: Partial<EventType>, token?: string): Promise<EventType>;
export function deleteEventType(id: string, token?: string): Promise<void>;
```

## Dependencies { .dependencies }

### visionarias-client 0.1.0 { .dependency }

AI Sales & Marketing Platform frontend providing the scheduling event types API for booking and calendar management.

[@satisfied-by](visionarias-client)
