# UI-SPEC — PR-{N}-{slug}

> Owner: `ux-flow-architect`. Solo si PR tiene superficie UI. Frontend builder consume esto + CONTRACT.md.

## Screens / componentes nuevos

| Screen | Path frontend | Server/Client | Notas |
|---|---|---|---|
| ... | `app/(...)/...` | Server | ... |

## Component tree

```
PageX (Server)
├── DataFetcher (Server)
└── ClientShell (Client)
    ├── FilterBar
    ├── DataTable
    └── DetailDrawer
```

## Data flow

- Server fetch → ... → Client render
- Mutations: useMutation(...) → API endpoint X
- Optimistic updates: ...

## Interaction patterns

| Acción | Trigger | Resultado |
|---|---|---|
| ... | ... | ... |

## Responsive

- Mobile: ...
- Desktop: ...

## Shadcn UI components

- ...

## Tokens / Tailwind

- Colores: ...
- Espaciado: ...

## States

- Loading: skeleton ...
- Empty: ...
- Error: ...

## Accessibility

- ...

## Open questions for PM

- ...

---

<!-- @pm: UI-SPEC.md ready. Próximo paso: ejecutar prompts/02-builder-start.md (frontend) o ejecutar /pm "PR-N ux done" para review. -->
