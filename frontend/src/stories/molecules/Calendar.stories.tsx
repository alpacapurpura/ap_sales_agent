import React from 'react';
import type { Meta, StoryObj } from '@storybook/nextjs-vite';
import { Calendar } from '@/components/ui/calendar';

const meta = {
  title: 'Molecules/Calendar',
  component: Calendar,
  tags: ['autodocs'],
} satisfies Meta<typeof Calendar>;

export default meta;
type Story = StoryObj<typeof meta>;

function CalendarDemo() {
  const [date, setDate] = React.useState<Date | undefined>(new Date());
  return (
    <Calendar
      mode="single"
      selected={date}
      onSelect={setDate}
      className="rounded-md border"
    />
  );
}

export const Default: Story = {
  render: () => <CalendarDemo />,
};
