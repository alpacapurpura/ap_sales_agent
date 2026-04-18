import { fn } from "storybook/test";

import { LogoKitPlaceholder } from "../placeholders";

import type { Meta, StoryObj } from "@storybook/nextjs-vite";

const meta = {
  title: "Brand Studio/Actions/LogoKit",
  component: LogoKitPlaceholder,
  tags: ["autodocs"],
  args: {
    value: undefined,
    onChange: fn(),
  },
} satisfies Meta<typeof LogoKitPlaceholder>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
