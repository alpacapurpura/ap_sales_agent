import { fn } from "storybook/test";

import { SectionPage } from "../SectionPage";

import type { Meta, StoryObj } from "@storybook/nextjs-vite";

const IDENTITY_SCHEMA = {
  key: "brand.identity",
  title: "Identidad",
  description: "Los cimientos de tu marca.",
  fields: [
    {
      id: "brand_name",
      label: "Nombre",
      type: "text" as const,
      path: "brand_name",
      required: true,
    },
    { id: "tagline", label: "Tagline", type: "text" as const, path: "tagline" },
    {
      id: "description",
      label: "Descripción",
      type: "textarea" as const,
      path: "description",
      rows: 4,
    },
    {
      id: "website",
      label: "Sitio web",
      type: "url" as const,
      path: "website",
    },
  ],
};

const meta = {
  title: "Brand Studio/Pages/SectionPage",
  component: SectionPage,
  tags: ["autodocs"],
  parameters: {
    nextjs: {
      appDirectory: true,
      navigation: {
        pathname: "/t-demo/brand-studio/identity",
        segments: [["tenantId", "t-demo"]],
      },
    },
  },
  args: {
    sectionSlug: "identity",
    schema: IDENTITY_SCHEMA,
    onSave: fn(),
  },
} satisfies Meta<typeof SectionPage>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    values: { brand_name: "", tagline: "", description: "", website: "" },
  },
};

export const Populated: Story = {
  args: {
    values: {
      brand_name: "Visionarias",
      tagline: "Creadoras que viven de lo que aman",
      description:
        "Ayudamos a creadoras digitales a transformar su audiencia en clientes recurrentes con sistemas de contenido + venta consultiva.",
      website: "https://visionarias.example",
    },
  },
};

export const Loading: Story = {
  args: {
    values: undefined,
    isLoading: true,
  },
};
