import { fn } from "storybook/test";

import { SingleImagePickerPlaceholder } from "../placeholders";

import type { Meta, StoryObj } from "@storybook/nextjs-vite";

const meta = {
  title: "Brand Studio/Actions/SingleImagePicker",
  component: SingleImagePickerPlaceholder,
  tags: ["autodocs"],
  args: {
    value: "",
    onChange: fn(),
  },
} satisfies Meta<typeof SingleImagePickerPlaceholder>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};
