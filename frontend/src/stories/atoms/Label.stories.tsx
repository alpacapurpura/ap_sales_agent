import { Label } from "@/components/ui/label";

import type { Meta, StoryObj } from "@storybook/nextjs-vite";

const meta = {
  title: "Atoms/Label",
  component: Label,
  tags: ["autodocs"],
} satisfies Meta<typeof Label>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = { args: { children: "Email address" } };
