import type { Meta, StoryObj } from '@storybook/nextjs-vite';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';

const tags = Array.from({ length: 50 }).map((_, i) => `v1.${i}.0`);

const meta = {
  title: 'Atoms/ScrollArea',
  component: ScrollArea,
  tags: ['autodocs'],
} satisfies Meta<typeof ScrollArea>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <ScrollArea className="h-[200px] w-[350px] rounded-md border p-4">
      <h4 className="mb-4 text-sm font-medium leading-none">Tags</h4>
      {tags.map((tag) => (
        <div key={tag}>
          <div className="text-sm">{tag}</div>
          <Separator className="my-2" />
        </div>
      ))}
    </ScrollArea>
  ),
};
