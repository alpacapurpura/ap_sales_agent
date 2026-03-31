
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { OfferCard } from '../components/dashboard/offer-card';
import { MOCK_OFFER_NORMALIZED } from './fixtures';

// Mock Next.js router
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
  useParams: () => ({ tenantId: 'visionarias' }),
}));

// Mock NavigationProvider context
vi.mock('@/components/shared/navigation', () => ({
  useNavigation: () => ({ navigate: vi.fn(), isNavigating: false, navigateReplace: vi.fn(), pendingHref: null }),
}));

describe('OfferCard Component', () => {
  it('renders the offer name correctly', () => {
    render(<OfferCard offer={MOCK_OFFER_NORMALIZED} />);
    
    // The most critical check: Is the name visible?
    expect(screen.getByText("Guía: Liberar la Mente")).toBeInTheDocument();
  });

  it('renders the correct archetype label', () => {
    render(<OfferCard offer={MOCK_OFFER_NORMALIZED} />);

    // Should map archetype "producto" -> "Producto" via ARCHETYPE_METADATA
    expect(screen.getByText("Producto")).toBeInTheDocument();
  });

  it('renders the correct delivery badge', () => {
    render(<OfferCard offer={MOCK_OFFER_NORMALIZED} />);
    expect(screen.getByText("DIY")).toBeInTheDocument();
  });
});
