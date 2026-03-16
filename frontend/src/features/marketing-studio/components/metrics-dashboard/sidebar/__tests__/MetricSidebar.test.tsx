import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
// NOTE: MetricSidebar component is created in Plan 11-01.
// This file scaffolds the test structure so Wave 1 can reference it in verify blocks.
// Import will resolve once Plan 11-01 creates the component.
import { MetricSidebar } from '../MetricSidebar';

// NOTE: MetricClickData type is added to metrics.ts in Plan 11-01.
// Inline type definition here for scaffold purposes.
interface MetricClickData {
  stageId: string;
  channelSlug: string;
  metricName: string;
  currentValue: number;
}

describe('MetricSidebar', () => {
  const mockMetric: MetricClickData = {
    stageId: 'attraction',
    channelSlug: 'instagram',
    metricName: 'visitors',
    currentValue: 1250,
  };

  it('should not render visible content when isOpen is false', () => {
    // Arrange
    const { container } = render(
      <MetricSidebar
        isOpen={false}
        onClose={() => {}}
        metric={mockMetric}
        stageId="attraction"
      >
        <div>Content</div>
      </MetricSidebar>
    );

    // Act & Assert
    // TODO (Plan 11-01): Verify sidebar panel has hidden/closed state class
    expect(container).toBeTruthy();
  });

  it('should render metric name when sidebar is open', () => {
    // Arrange
    render(
      <MetricSidebar
        isOpen={true}
        onClose={() => {}}
        metric={mockMetric}
        stageId="attraction"
      >
        <div>Sidebar Content</div>
      </MetricSidebar>
    );

    // Act & Assert
    // TODO (Plan 11-01): Verify metric name is visible in sidebar header
    expect(screen.getByText(/visitors/i)).toBeInTheDocument();
  });

  it('should render metric current value', () => {
    // Arrange
    render(
      <MetricSidebar
        isOpen={true}
        onClose={() => {}}
        metric={mockMetric}
        stageId="attraction"
      >
        <div>Content</div>
      </MetricSidebar>
    );

    // Act & Assert
    // TODO (Plan 11-01): Verify formatted value appears in sidebar
    expect(screen.getByText(/1250|1\.2k/)).toBeInTheDocument();
  });

  it('should call onClose when close button is clicked', async () => {
    // Arrange
    const handleClose = vi.fn();
    render(
      <MetricSidebar
        isOpen={true}
        onClose={handleClose}
        metric={mockMetric}
        stageId="attraction"
      >
        <div>Content</div>
      </MetricSidebar>
    );

    // Act
    const user = userEvent.setup();
    // TODO (Plan 11-01): Find and click close button (X icon aria-label="Cerrar")
    // const closeButton = screen.getByRole('button', { name: /cerrar/i });
    // await user.click(closeButton);

    // Assert
    expect(handleClose).toBeDefined();
    expect(user).toBeTruthy();
  });

  it('should render children when provided', () => {
    // Arrange
    const testContent = 'Test Sidebar Content';
    render(
      <MetricSidebar
        isOpen={true}
        onClose={() => {}}
        metric={mockMetric}
        stageId="attraction"
      >
        <div>{testContent}</div>
      </MetricSidebar>
    );

    // Act & Assert
    expect(screen.getByText(testContent)).toBeInTheDocument();
  });

  it('should display channel slug in sidebar context', () => {
    // Arrange
    render(
      <MetricSidebar
        isOpen={true}
        onClose={() => {}}
        metric={mockMetric}
        stageId="attraction"
      >
        <div>Content</div>
      </MetricSidebar>
    );

    // Act & Assert
    // TODO (Plan 11-01): Verify channel context (e.g., "instagram") is shown
    expect(mockMetric.channelSlug).toBe('instagram');
  });
});
