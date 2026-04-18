import { fn } from "storybook/test";

import { FormRuntimeProvider } from "@/components/form-runtime";
import { ThemeInjectorAction } from "@/features/brand-studio/actions/ThemeInjectorAction";

import type { SectionSchema } from "@/lib/form-runtime/schema";
import type { Meta, StoryObj } from "@storybook/nextjs-vite";

const VISUALS_SCHEMA: SectionSchema = {
  key: "brand.visuals",
  title: "Visuales",
  fields: [{ id: "primary_color", label: "Primario", type: "text", path: "primary_color" }],
};

interface ThemeInjectorStoryArgs {
  values: Record<string, unknown>;
}

function ThemeInjectorStory({ values }: ThemeInjectorStoryArgs) {
  return (
    <FormRuntimeProvider schema={VISUALS_SCHEMA} initialValues={values} onSave={fn()}>
      <ThemeInjectorAction value={undefined} onChange={fn()} />
    </FormRuntimeProvider>
  );
}

const meta = {
  title: "Brand Studio/Actions/ThemeInjector",
  component: ThemeInjectorStory,
  tags: ["autodocs"],
} satisfies Meta<typeof ThemeInjectorStory>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: { values: {} },
};

export const Populated: Story = {
  args: {
    values: {
      primary_color: "#0f172a",
      secondary_color: "#2563eb",
      accent_color: "#f59e0b",
      font_heading: "Inter",
      font_body: "Roboto",
    },
  },
};
