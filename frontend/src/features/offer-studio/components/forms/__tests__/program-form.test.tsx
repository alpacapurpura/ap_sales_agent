import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ProgramDetailsForm } from '../program-form';
import { useForm } from 'react-hook-form';
import { Form } from '@/components/ui/form';
import { OfferFormValues, ProgramStructure, OfferStatus, OfferType } from '../../../types/schema';

// Mock complex UI components to avoid JSDOM issues
vi.mock('@/components/ui/smart-datetime-picker', () => ({
  SmartDateTimePicker: () => <div data-testid="smart-datetime-picker">Picker</div>
}));

vi.mock('@/components/ui/timezone-select', () => ({
  TimezoneSelect: () => <div data-testid="timezone-select">Timezone</div>
}));

vi.mock('@/components/ui/rich-select', () => ({
  RichSelect: () => <div data-testid="rich-select">Select</div>
}));

function Wrapper() {
  const form = useForm<OfferFormValues>({
    defaultValues: {
      public_name: "Test Offer",
      status: OfferStatus.DRAFT,
      type: OfferType.COHORT_BASED_COURSE,
      specific_details: {
        structure_type: ProgramStructure.FIXED_DATE_COHORT,
        schedule: []
      }
    }
  });

  return (
    <Form {...form}>
      <ProgramDetailsForm form={form} />
    </Form>
  );
}

describe('ProgramDetailsForm', () => {
  it('renders without crashing', () => {
    render(<Wrapper />);
    
    // Check for the section headers we added/modified
    expect(screen.getByText('Estructura y Admisión')).toBeDefined();
    expect(screen.getByText('Calendario de Lanzamiento')).toBeDefined();
    
    // Check for the Labels we fixed (they should be rendered as Label now)
    expect(screen.getByText('Fecha y Hora de Inicio (Kick-off)')).toBeDefined();
    expect(screen.getByText('Fecha de Fin (Graduación)')).toBeDefined();
  });
});
