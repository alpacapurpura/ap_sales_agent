import type { Meta, StoryObj } from '@storybook/nextjs-vite';
import { Textarea } from '@/components/ui/textarea';

const meta = {
  title: 'Atoms/Textarea',
  component: Textarea,
  tags: ['autodocs'],
} satisfies Meta<typeof Textarea>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = { args: { placeholder: 'Type your message here' } };
export const Disabled: Story = { args: { placeholder: 'Disabled', disabled: true } };
