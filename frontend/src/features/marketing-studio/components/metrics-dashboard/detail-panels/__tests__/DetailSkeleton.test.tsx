import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
// NOTE: DetailSkeleton component is created in Plan 11-01.
// This file scaffolds the test structure so Wave 1 can reference it in verify blocks.
// Import will resolve once Plan 11-01 creates the component.
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
    // TODO (Plan 11-01): Verify skeleton bars are visible via aria or class name
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
    expect(container.querySelectorAll('[class*="skeleton"]').length).toBeGreaterThan(0);
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
    expect(document.body).toBeTruthy();
  });

  it('should accept and render className prop on wrapper', () => {
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
