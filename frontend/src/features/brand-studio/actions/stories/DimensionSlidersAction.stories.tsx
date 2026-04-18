import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fn } from "storybook/test";

import { DimensionSlidersAction } from "@/features/brand-studio/actions/DimensionSlidersAction";

import type { Meta, StoryObj } from "@storybook/nextjs-vite";

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

const meta = {
  title: "Brand Studio/Actions/DimensionSliders",
  component: DimensionSlidersAction,
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
} satisfies Meta<typeof DimensionSlidersAction>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const Populated: Story = {
  args: {
    value: {
      energy: 0.75,
      warmth: 0.5,
      humor: 0.25,
      expressiveness: 0.75,
      narrative: 0.5,
      verbosity: 0.25,
    },
  },
};
