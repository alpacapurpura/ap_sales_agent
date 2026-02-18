import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ValueStackSection } from '../ValueStackSection';
import { useForm } from 'react-hook-form';
import { Form } from '@/components/ui/form';
import { DeliverableFormat } from '../../../types';

// Mock RichSelect
vi.mock('@/components/ui/rich-select', () => ({
  RichSelect: ({ value, onValueChange }: any) => (
    <select data-testid="format-select" value={value} onChange={e => onValueChange(e.target.value)}>
      <option value="RECORDED_CONTENT">Recorded Content</option>
    </select>
  )
}));

// Mock icons
vi.mock('lucide-react', () => ({
  Plus: () => <span>+</span>,
  Trash2: () => <span>Del</span>
}));

const TestWrapper = () => {
  const form = useForm({
    defaultValues: {
      includes_offers: [],
      deliverables: [{
        name: "Test Item",
        format: DeliverableFormat.RECORDED_CONTENT,
        quantity: "1",
        value_stack_price: 100
      }]
    }
  });

  return (
    <Form {...form}>
      <ValueStackSection form={form} />
    </Form>
  );
};

describe('ValueStackSection', () => {
  it('handles numeric input updates without crashing', () => {
    render(<TestWrapper />);
    
    const input = screen.getByLabelText('Valor ($)');
    
    expect(input).toBeDefined();
    expect(input).toHaveValue(100);
    
    // Simulate user clearing input -> Should result in 0 (based on our fix)
    fireEvent.change(input, { target: { value: '' } });
    expect(input).toHaveValue(0);
    
    // Simulate valid input
    fireEvent.change(input, { target: { value: '500' } });
    expect(input).toHaveValue(500);
  });
});
