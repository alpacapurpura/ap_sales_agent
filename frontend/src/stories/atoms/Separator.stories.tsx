import type { Meta, StoryObj } from '@storybook/nextjs-vite';
import { Separator } from '@/components/ui/separator';

const meta = {
  title: 'Atoms/Separator',
  component: Separator,
  tags: ['autodocs'],
} satisfies Meta<typeof Separator>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Horizontal: Story = {
  render: () => (
    <div className="space-y-1">
      <h4 className="text-sm font-medium leading-none">Radix Primitives</h4>
      <p className="text-sm text-muted-foreground">An open-source UI component library.</p>
      <Separator className="my-4" />
      <p className="text-sm text-muted-foreground">Accessible. Customizable. Open Source.</p>
    </div>
  ),
};

export const Vertical: Story = {
  render: () => (
    <div className="flex h-5 items-center space-x-4 text-sm">
      <div>Blog</div>
      <Separator orientation="vertical" />
      <div>Docs</div>
      <Separator orientation="vertical" />
      <div>Source</div>
    </div>
  ),
};
