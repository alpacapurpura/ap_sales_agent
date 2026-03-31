
import { describe, it, expect } from 'vitest';
import { backendToFrontend } from '../api/adapter';
import { MOCK_BACKEND_RESPONSE } from './fixtures';
import { OfferType, OfferStatus } from '../types';

describe('Dashboard Logic & Adapter', () => {
  it('Adapter normalizes "public_name" to "name"', () => {
    const result = backendToFrontend(MOCK_BACKEND_RESPONSE as any);
    expect(result.name).toBe("Guía: Liberar la Mente");
  });

  it('Adapter maps backend status "active" to OfferStatus.ACTIVE', () => {
    const result = backendToFrontend(MOCK_BACKEND_RESPONSE as any);
    expect(result.status).toBe(OfferStatus.ACTIVE);
  });

  it('Adapter handles unknown Enums gracefully', () => {
    const weirdData = { ...MOCK_BACKEND_RESPONSE, type: "UNKNOWN_TYPE_XYZ" };
    const result = backendToFrontend(weirdData as any);
    
    // Should fallback to default (FREE_RESOURCE) instead of crashing
    expect(result.type).toBe(OfferType.FREE_RESOURCE);
  });
});
