import { Input } from "@/components/ui/input";

import type { Meta, StoryObj } from "@storybook/nextjs-vite";

const meta = {
  title: "Atoms/Input",
  component: Input,
  tags: ["autodocs"],
} satisfies Meta<typeof Input>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = { args: { placeholder: "Type something..." } };
export const Email: Story = { args: { type: "email", placeholder: "Email" } };
export const Disabled: Story = { args: { placeholder: "Disabled", disabled: true } };
export const File: Story = { args: { type: "file" } };
