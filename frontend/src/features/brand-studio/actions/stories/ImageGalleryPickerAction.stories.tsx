import { fn } from "storybook/test";

import { ImageGalleryPickerPlaceholder } from "../placeholders";

import type { Meta, StoryObj } from "@storybook/nextjs-vite";

/**
 * Placeholder story — Sprint 2.1 replaces the component reference with the
 * ported `ImageGalleryPickerAction`. `args.value` / `args.onChange` already
 * follow the ActionComponent contract so the real action drops in without
 * touching this file's shape.
 */
const meta = {
  title: "Brand Studio/Actions/ImageGalleryPicker",
  component: ImageGalleryPickerPlaceholder,
  tags: ["autodocs"],
  args: {
    value: "",
    onChange: fn(),
  },
} satisfies Meta<typeof ImageGalleryPickerPlaceholder>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
