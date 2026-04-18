import { fn } from "storybook/test";

import { DimensionSlidersPlaceholder } from "../placeholders";

import type { Meta, StoryObj } from "@storybook/nextjs-vite";

const meta = {
  title: "Brand Studio/Actions/DimensionSliders",
  component: DimensionSlidersPlaceholder,
  tags: ["autodocs"],
  args: {
    value: undefined,
    onChange: fn(),
  },
} satisfies Meta<typeof DimensionSlidersPlaceholder>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
