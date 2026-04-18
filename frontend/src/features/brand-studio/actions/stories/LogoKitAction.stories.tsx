import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fn } from "storybook/test";

import { LogoKitAction } from "@/features/brand-studio/actions/LogoKitAction";

import type { Meta, StoryObj } from "@storybook/nextjs-vite";

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

const meta = {
  title: "Brand Studio/Actions/LogoKit",
  component: LogoKitAction,
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
} satisfies Meta<typeof LogoKitAction>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const Populated: Story = {
  args: {
    value: {
      primary: "https://picsum.photos/seed/logo-primary/800/400",
      secondary: "https://picsum.photos/seed/logo-iso/400/400",
      dark_mode: "https://picsum.photos/seed/logo-dark/800/400",
      light_mode: "https://picsum.photos/seed/logo-light/800/400",
    },
  },
};
