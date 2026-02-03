
import { render, screen } from '@testing-library/react';
import { useForm } from 'react-hook-form';
import { PromiseStep } from './promise-step';
import { Form } from '@/components/ui/form';
import { OfferFormValues } from '../../types/schema';

// Mock ResizeObserver for Textarea
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

function TestWrapper({ defaultValues }: { defaultValues: any }) {
  const form = useForm<OfferFormValues>({
    defaultValues,
  });

  return (
    <Form {...form}>
      <form>
        <PromiseStep form={form} />
      </form>
    </Form>
  );
}

describe('PromiseStep', () => {
  it('renders correctly with valid data', () => {
    const defaultValues = {
      headline_promise: 'Test Promise',
      primary_outcome: 'Test Outcome',
      time_to_value: 'Test Time',
      target_avatar_match: ['Test Avatar'],
    };

    render(<TestWrapper defaultValues={defaultValues} />);
    expect(screen.getByDisplayValue('Test Promise')).toBeInTheDocument();
  });

  it('renders correctly even when primary_outcome is null (Fixed)', () => {
    const defaultValues = {
      headline_promise: 'Test Promise',
      primary_outcome: null, // This used to trigger the error
      time_to_value: null,
      target_avatar_match: [],
    };

    // Spy on console.error to ensure no warnings are logged
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    render(<TestWrapper defaultValues={defaultValues} />);
    
    // Check that inputs are empty (value is "")
    // When value is "", placeholder is shown.
    // Or we can check display value is empty string.
    
    const outcomeInput = screen.getByPlaceholderText('Sistema de ventas instalado');
    expect(outcomeInput).toHaveValue('');
    
    const timeInput = screen.getByPlaceholderText('3 semanas');
    expect(timeInput).toHaveValue('');

    // Ensure no console errors (especially the "value prop on input should not be null")
    expect(consoleSpy).not.toHaveBeenCalled();
    
    consoleSpy.mockRestore();
  });
});
