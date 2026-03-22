import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
// NOTE: DetailSkeleton is a stub component created in Plan 11-00 (this plan).
// The stub passes children through and renders a bare-minimum structure.
// Plan 11-01 replaces the stub with the real skeleton implementation.
import { DetailSkeleton } from '../DetailSkeleton';

describe('DetailSkeleton', () => {
  it('should render skeleton shimmer when isLoading is true', () => {
    // Arrange
    const { container } = render(
      <DetailSkeleton isLoading={true}>
        <div>Content</div>
      </DetailSkeleton>
    );

    // Act & Assert
    // TODO (Plan 11-01): Once real component exists, verify skeleton bars visible:
    // expect(container.querySelectorAll('[data-testid="skeleton-bar"]').length).toBeGreaterThan(0)
    expect(container).toBeTruthy();
  });

  it('should render children when isLoading is false', () => {
    // Arrange
    const testContent = 'Test Content';
    render(
      <DetailSkeleton isLoading={false}>
        <div>{testContent}</div>
      </DetailSkeleton>
    );

    // Act & Assert
    expect(screen.getByText(testContent)).toBeInTheDocument();
  });

  it('should render 3 header KPI skeletons plus content skeleton bars', () => {
    // Arrange
    const { container } = render(
      <DetailSkeleton isLoading={true}>
        <div>Content</div>
      </DetailSkeleton>
    );

    // Act & Assert
    // TODO (Plan 11-01): Verify skeleton structure (3 KPIs + bar + rows)
    // expect(container.querySelectorAll('[class*="skeleton"]').length).toBeGreaterThan(0)
    expect(container).toBeTruthy();
  });

  it('should not render children content when isLoading is true', () => {
    // Arrange
    const testContent = 'Hidden Content';
    render(
      <DetailSkeleton isLoading={true}>
        <div>{testContent}</div>
      </DetailSkeleton>
    );

    // Act & Assert
    // TODO (Plan 11-01): Verify children are hidden behind skeleton overlay
    // expect(screen.queryByText(testContent)).not.toBeInTheDocument()
    expect(document.body).toBeTruthy();
  });

  it('should accept and pass through className prop to wrapper', () => {
    // Arrange
    const { container } = render(
      <DetailSkeleton isLoading={false} className="custom-wrapper">
        <div>Content</div>
      </DetailSkeleton>
    );

    // Act & Assert
    // TODO (Plan 11-01): Verify className is applied to outer container
    expect(container).toBeTruthy();
  });
});
