import { fn } from "storybook/test";

import { ThemeInjectorPlaceholder } from "../placeholders";

import type { Meta, StoryObj } from "@storybook/nextjs-vite";

const meta = {
  title: "Brand Studio/Actions/ThemeInjector",
  component: ThemeInjectorPlaceholder,
  tags: ["autodocs"],
  args: {
    value: undefined,
    onChange: fn(),
  },
} satisfies Meta<typeof ThemeInjectorPlaceholder>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
