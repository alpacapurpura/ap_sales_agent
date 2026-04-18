# Storybook conventions

Single source of truth for how stories are organized and named in this codebase. If you are adding a new story, this document tells you where it goes and what it must contain.

## Title hierarchy

Stories follow **Atomic Design** for generic UI primitives and **domain-prefixed paths** for feature-specific components. A story's `title` drives its position in the Storybook sidebar and must match the tables below exactly.

### Generic UI (project-wide, reusable anywhere)

| Sidebar path | What lives here | Example |
|---|---|---|
| `Tokens/<Name>` | Design tokens (colors, spacing, typography scales) | `Tokens/DesignTokens` |
| `Atoms/<Component>` | Primitive UI components with no composition | `Atoms/Button`, `Atoms/Input`, `Atoms/Badge` |
| `Molecules/<Component>` | Composed UI that wraps 1-3 atoms | `Molecules/Dialog`, `Molecules/Sheet` |
| `Organisms/<Component>` | Complex composed UI (often data-aware) | `Organisms/DataTable`, `Organisms/Form` |

### Form Runtime (shared form infrastructure)

| Sidebar path | What lives here | Example |
|---|---|---|
| `Form Runtime/Inputs/<Name>` | The 9 type-specific inputs (TextInput, EnumInput, ArrayInput, …) | `Form Runtime/Inputs/TextInput` |
| `Form Runtime/Components/<Name>` | Layout + context components (EditableField, SessionHeader, AutosaveBanner, FieldList, FieldDetail, UniversalEditableSection) | `Form Runtime/Components/AutosaveBanner` |

### Feature stories (domain-specific)

| Sidebar path | What lives here | Example |
|---|---|---|
| `Brand Studio/Actions/<Name>` | Rich actions referenced by brand-studio schemas | `Brand Studio/Actions/ImageGalleryPicker` |
| `Brand Studio/Pages/<Name>` | Page compositions (SectionPage + specific studios) | `Brand Studio/Pages/SectionPage` |
| `Offer Studio/Actions/<Name>` | (future) rich actions for offer-studio schemas | — |
| `Buyer Persona Studio/...` | (future) | — |

## File layout

**Colocation is the default.** New stories live next to their source file, in a sibling `stories/` directory when the feature already uses `__tests__/`.

```
src/
├── components/
│   ├── ui/                          (shadcn — stories in src/stories/atoms/, src/stories/molecules/)
│   └── form-runtime/
│       ├── EditableField.tsx
│       ├── __tests__/
│       │   └── EditableField.test.tsx
│       └── stories/
│           └── EditableField.stories.tsx          ← colocated
└── features/
    └── brand-studio/
        └── actions/
            ├── ImageGalleryPickerAction.tsx
            ├── __tests__/
            │   └── ImageGalleryPickerAction.test.tsx
            └── stories/
                └── ImageGalleryPickerAction.stories.tsx   ← colocated
```

Existing stories in `src/stories/atoms/`, `src/stories/molecules/`, `src/stories/organisms/`, `src/stories/tokens/` remain segregated — those predate this convention and do not need to be moved. New stories for new code are colocated.

Storybook's `stories` glob in `.storybook/main.ts` already picks up `src/**/*.stories.@(js|jsx|ts|tsx)` — both segregated and colocated files load automatically.

## Mandatory story shape

Every new story file MUST:

1. Import types from `@storybook/nextjs-vite`.
2. Declare a `meta` object with `title`, `component`, and `tags: ["autodocs"]`.
3. Route user-facing callbacks (`onChange`, `onClick`, `onSave`) through `fn()` from `@storybook/test` so they surface in the Actions panel.
4. Expose every meaningful prop in `argTypes` when the default Controls inference is wrong.
5. Keep `args` fixtures realistic (not `"test"` or `"lorem"`).

### Minimum exports per story file

| Component kind | Required stories |
|---|---|
| Atom / Molecule | `Default` |
| Form Runtime component | `Default` + `Populated` |
| Brand Studio Action | `Default` + `Populated`; add `Loading` + `Error` when the component has those states |
| Brand Studio Page | `Default`, `Populated`, and `Loading` |

### Reference template

```tsx
import { fn } from "@storybook/test";

import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import { ImageGalleryPickerAction } from "../ImageGalleryPickerAction";

const meta = {
  title: "Brand Studio/Actions/ImageGalleryPicker",
  component: ImageGalleryPickerAction,
  tags: ["autodocs"],
  args: {
    value: "",
    onChange: fn(),
  },
} satisfies Meta<typeof ImageGalleryPickerAction>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const Populated: Story = {
  args: { value: "https://example.com/avatar.png" },
};
```

## Accessibility

`addon-a11y` is enabled. Every new story must surface zero a11y violations by default. If a component has an unavoidable warning (color contrast on purpose, etc.), document it with a `parameters.a11y.config` exception in the story file with a comment explaining why.

## Quality gates

Before committing a story file:

```bash
cd frontend && npm run build-storybook    # must succeed
cd frontend && npx tsc --noEmit           # 0 errors
cd frontend && ./node_modules/.bin/eslint src/ --cache  # 0 errors on changed files
```

## Controls vs Actions

- **Controls panel** (from `args`) — for inputs users can change (value, disabled, label).
- **Actions panel** (from `fn()` in `args`) — for events the component fires (onChange, onSubmit). Never omit `onChange` when a component accepts it; otherwise the user has no way to confirm wiring works.
