import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fn } from "storybook/test";

import { SingleImagePickerAction } from "@/features/brand-studio/actions/SingleImagePickerAction";

import type { Meta, StoryObj } from "@storybook/nextjs-vite";

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

const meta = {
  title: "Brand Studio/Actions/SingleImagePicker",
  component: SingleImagePickerAction,
  tags: ["autodocs"],
  decorators: [
    (Story) => (
      <QueryClientProvider client={queryClient}>
        <Story />
      </QueryClientProvider>
    ),
  ],
  args: {
    value: "",
    onChange: fn(),
  },
} satisfies Meta<typeof SingleImagePickerAction>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const Populated: Story = {
  args: {
    value: "https://picsum.photos/seed/brand-logo/800/400",
  },
};
