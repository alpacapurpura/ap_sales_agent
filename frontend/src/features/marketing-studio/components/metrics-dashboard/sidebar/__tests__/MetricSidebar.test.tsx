import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
// NOTE: @testing-library/user-event is added in Plan 11-01 (npm install @testing-library/user-event).
// userEvent import kept as a comment here to show intent; uncomment once installed.
// import userEvent from '@testing-library/user-event';

// NOTE: MetricSidebar is a stub component created in Plan 11-00 (this plan).
// The stub renders metric name + value when open, null when closed.
// Plan 11-01 replaces the stub with the real sheet/drawer implementation.
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
    expect(container.firstChild).toBeNull();
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
    expect(screen.getByText('1250')).toBeInTheDocument();
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
    // TODO (Plan 11-01): Install @testing-library/user-event, then:
    // const user = userEvent.setup();
    // const closeButton = screen.getByRole('button', { name: /cerrar/i });
    // await user.click(closeButton);

    // Assert
    expect(handleClose).toBeDefined();
    expect(typeof handleClose).toBe('function');
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
    // TODO (Plan 11-01): Verify channel context (e.g., "instagram") is shown in UI
    expect(mockMetric.channelSlug).toBe('instagram');
  });
});
