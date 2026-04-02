import type { Meta, StoryObj } from '@storybook/nextjs-vite';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';

const meta = {
  title: 'Molecules/Sheet',
  component: Sheet,
  tags: ['autodocs'],
  argTypes: {
    side: {
      control: 'select',
      options: ['top', 'right', 'bottom', 'left'],
    },
  },
} satisfies Meta<typeof Sheet>;

export default meta;
type Story = StoryObj<typeof meta>;

const SheetDemo = ({ side = 'right' }: { side?: 'top' | 'right' | 'bottom' | 'left' }) => (
  <Sheet>
    <SheetTrigger asChild>
      <Button variant="outline">Open {side}</Button>
    </SheetTrigger>
    <SheetContent side={side}>
      <SheetHeader>
        <SheetTitle>Sheet Title</SheetTitle>
        <SheetDescription>
          This is a sheet that slides in from the {side}.
        </SheetDescription>
      </SheetHeader>
      <div className="py-4">
        <p>Sheet content goes here.</p>
      </div>
    </SheetContent>
  </Sheet>
);

export const Right: Story = { render: () => <SheetDemo side="right" /> };
export const Left: Story = { render: () => <SheetDemo side="left" /> };
export const Top: Story = { render: () => <SheetDemo side="top" /> };
export const Bottom: Story = { render: () => <SheetDemo side="bottom" /> };
