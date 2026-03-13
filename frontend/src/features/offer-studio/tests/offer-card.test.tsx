
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { OfferCard } from '../components/dashboard/offer-card';
import { MOCK_OFFER_NORMALIZED } from './fixtures';

// Mock Next.js router
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
  useParams: () => ({ tenantId: 'visionarias' }),
}));

describe('OfferCard Component', () => {
  it('renders the offer name correctly', () => {
    render(<OfferCard offer={MOCK_OFFER_NORMALIZED} />);
    
    // The most critical check: Is the name visible?
    expect(screen.getByText("Guía: Liberar la Mente")).toBeInTheDocument();
  });

  it('renders the correct type label', () => {
    render(<OfferCard offer={MOCK_OFFER_NORMALIZED} />);
    
    // Should map FREE_RESOURCE -> "Recurso Gratuito" via metadata
    expect(screen.getByText("Recurso Gratuito")).toBeInTheDocument();
  });

  it('renders the correct delivery badge', () => {
    render(<OfferCard offer={MOCK_OFFER_NORMALIZED} />);
    expect(screen.getByText("DIY")).toBeInTheDocument();
  });
});
