import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fn } from "storybook/test";

import { PresetCatalogAction } from "@/features/brand-studio/actions/PresetCatalogAction";

import type { Meta, StoryObj } from "@storybook/nextjs-vite";

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

const meta = {
  title: "Brand Studio/Actions/PresetCatalog",
  component: PresetCatalogAction,
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
} satisfies Meta<typeof PresetCatalogAction>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const Populated: Story = {
  args: { value: "sage" },
};
