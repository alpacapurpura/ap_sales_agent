import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { SessionScheduleBuilder } from '../session-schedule-builder';
import { useForm } from 'react-hook-form';
import { Form } from '@/components/ui/form';
import { OfferFormValues } from '../../../../../types/schema';
import { ProgramStructure, OfferStatus, OfferType } from '../../../../../types';

// Wrapper component to provide Form context
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
      <SessionScheduleBuilder form={form} />
    </Form>
  );
}

describe('SessionScheduleBuilder', () => {
  it('renders without crashing and shows empty state', () => {
    render(<Wrapper />);
    expect(screen.getByText('Horario de Sesiones')).toBeDefined();
    expect(screen.getByText('No hay sesiones configuradas')).toBeDefined();
  });

  it('can add a session', () => {
    render(<Wrapper />);
    const addButton = screen.getByText('Crear primera sesión');
    fireEvent.click(addButton);

    // Should now see input fields
    expect(screen.getByText('Título de la Sesión')).toBeDefined();
    expect(screen.getByText('Día')).toBeDefined();
    expect(screen.getByText('Hora')).toBeDefined();
  });

  it('can remove a session', () => {
    render(<Wrapper />);
    
    // Add a session first
    const addButton = screen.getByText('Agregar Sesión');
    fireEvent.click(addButton);
    
    // Check it exists
    expect(screen.getAllByText('Título de la Sesión')).toHaveLength(1);

    // Find delete button (Trash2 icon usually inside a button)
    // We can find by role button and then check it has svg inside, or use testid if we added one.
    // For now, let's look for the button that is likely the delete button (not the Add button)
    const buttons = screen.getAllByRole('button');
    // Filter out the 'Agregar Sesión' button and select trigger
    const deleteBtn = buttons.find(b => !b.textContent?.includes('Agregar') && !b.textContent?.includes('Lunes'));
    
    if (deleteBtn) {
      fireEvent.click(deleteBtn);
    }
    
    // Should be empty again
    expect(screen.queryByText('Título de la Sesión')).toBeNull();
  });

  it('can add multiple sessions', () => {
    render(<Wrapper />);
    
    const addButton = screen.getByText('Agregar Sesión');
    fireEvent.click(addButton);
    
    // Now the button is at the top right
    const topAddButton = screen.getByText('Agregar Sesión');
    fireEvent.click(topAddButton);
    
    expect(screen.getAllByText('Título de la Sesión')).toHaveLength(2);
  });
});
