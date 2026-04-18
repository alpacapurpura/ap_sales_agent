import { fn } from "storybook/test";

import { PresetCatalogPlaceholder } from "../placeholders";

import type { Meta, StoryObj } from "@storybook/nextjs-vite";

const meta = {
  title: "Brand Studio/Actions/PresetCatalog",
  component: PresetCatalogPlaceholder,
  tags: ["autodocs"],
  args: {
    value: "",
    onChange: fn(),
  },
} satisfies Meta<typeof PresetCatalogPlaceholder>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
