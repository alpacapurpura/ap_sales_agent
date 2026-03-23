# ASCII Mockup Conventions

Use these conventions for all layout mockups in Phase 5 proposals and Phase 7 UI-SPEC.

## Box Drawing Characters

```
┌──────────────────┐    Top-left, horizontal, top-right
│                  │    Vertical sides
├──────────────────┤    Left-tee, horizontal, right-tee (divider)
│                  │
└──────────────────┘    Bottom-left, horizontal, bottom-right
```

Nested boxes:
```
┌─────────────────────────────┐
│  ┌─────────┐  ┌─────────┐  │
│  │  Card A  │  │  Card B  │  │
│  └─────────┘  └─────────┘  │
└─────────────────────────────┘
```

## Component Notation

| Convention | Meaning | Example |
|---|---|---|
| `[ComponentName]` | React component | `[MetricCard]` |
| `{field_name}` | Dynamic data field | `{total_leads}` |
| `"Button Label"` | Clickable element with label | `"Save Changes"` |
| `( ) Option` | Radio button | `( ) Monthly` |
| `[x] Option` | Checkbox (checked) | `[x] Active` |
| `[ ] Option` | Checkbox (unchecked) | `[ ] Draft` |
| `[▼ Dropdown]` | Select/dropdown | `[▼ Last 30 days]` |
| `[🔍 ______]` | Search input | `[🔍 Search leads...]` |
| `───────` | Separator/divider | `───────────` |
| `█████░░░` | Progress bar | `████████░░ 80%` |
| `📊 📈 📉` | Chart placeholder | `📊 [LineChart]` |

## Layout Patterns

### Full-Width with Header
```
┌─────────────────────────────────────────────┐
│  Page Title                    "Action Btn"  │
├─────────────────────────────────────────────┤
│                                             │
│  [MainContent]                              │
│                                             │
└─────────────────────────────────────────────┘
```

### Sidebar + Main
```
┌───────────┬─────────────────────────────────┐
│           │                                 │
│ [Sidebar] │  [MainContent]                  │
│           │                                 │
│  Nav Item │  ┌───────────┐ ┌───────────┐   │
│  Nav Item │  │  Card A   │ │  Card B   │   │
│  Nav Item │  └───────────┘ └───────────┘   │
│           │                                 │
└───────────┴─────────────────────────────────┘
```

### Card Grid (2-3 columns)
```
┌─────────────────────────────────────────────┐
│  Section Title                              │
├─────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ {metric}  │  │ {metric}  │  │ {metric}  │  │
│  │ {label}   │  │ {label}   │  │ {label}   │  │
│  └──────────┘  └──────────┘  └──────────┘  │
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Card     │  │  Card     │  │  Card     │  │
│  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────┘
```

### Wizard / Stepper
```
┌─────────────────────────────────────────────┐
│  Step 1 ──● Step 2 ──○ Step 3 ──○ Step 4   │
├─────────────────────────────────────────────┤
│                                             │
│  Step Title                                 │
│  Step description text                      │
│                                             │
│  {form_field_1}  _______________            │
│  {form_field_2}  _______________            │
│                                             │
│            "Back"          "Next"            │
└─────────────────────────────────────────────┘
```

### Split View
```
┌────────────────────┬────────────────────────┐
│                    │                        │
│  [LeftPanel]       │  [RightPanel]          │
│                    │                        │
│  List Item 1  ►    │  Detail for Item 1     │
│  List Item 2       │  {field}: {value}      │
│  List Item 3       │  {field}: {value}      │
│                    │                        │
└────────────────────┴────────────────────────┘
```

## Sizing Guidelines

- Desktop mockup width: ~50-60 characters
- Mobile mockup width: ~30 characters
- Use consistent indentation (2 spaces)
- Keep mockups focused — show structure, not every pixel

## Desktop vs Mobile

Always show both when relevant:

```
DESKTOP (≥1024px):
┌───────────┬─────────────────────┐
│ [Sidebar] │ [Content]           │
└───────────┴─────────────────────┘

MOBILE (<768px):
┌─────────────────────┐
│ [☰ Menu]            │
├─────────────────────┤
│ [Content]           │
│ (full width)        │
└─────────────────────┘
```

## Tips

- Keep it readable — mockups are communication tools, not pixel-perfect designs
- Use `...` for repeated content: `│  Card  │  Card  │  ...  │`
- Mark interactive elements clearly with quotes: `"Click me"`
- Show data hierarchy through nesting depth
- Add annotations with `←` arrows when needed: `[Component] ← scrollable`
