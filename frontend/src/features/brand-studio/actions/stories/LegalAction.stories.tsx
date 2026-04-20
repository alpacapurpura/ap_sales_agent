import { fn } from "storybook/test";

import { LegalActionPlaceholder } from "../placeholders";

import type { Meta, StoryObj } from "@storybook/nextjs-vite";

const meta = {
  title: "Brand Studio/Actions/Legal",
  component: LegalActionPlaceholder,
  tags: ["autodocs"],
  args: {
    value: undefined,
    onChange: fn(),
  },
} satisfies Meta<typeof LegalActionPlaceholder>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
