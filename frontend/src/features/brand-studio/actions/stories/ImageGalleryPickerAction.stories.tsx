import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fn } from "storybook/test";

import { ImageGalleryPickerAction } from "@/features/brand-studio/actions/ImageGalleryPickerAction";

import type { Meta, StoryObj } from "@storybook/nextjs-vite";

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

const meta = {
  title: "Brand Studio/Actions/ImageGalleryPicker",
  component: ImageGalleryPickerAction,
  tags: ["autodocs"],
  decorators: [
    (Story) => (
      <QueryClientProvider client={queryClient}>
        <Story />
      </QueryClientProvider>
    ),
  ],
  args: {
    value: null,
    onChange: fn(),
  },
} satisfies Meta<typeof ImageGalleryPickerAction>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const Populated: Story = {
  args: {
    value: [
      "https://picsum.photos/seed/team-1/400/400",
      "https://picsum.photos/seed/team-2/400/400",
      "https://picsum.photos/seed/team-3/400/400",
    ],
  },
};
