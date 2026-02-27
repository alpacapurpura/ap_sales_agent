# UI/UX Proposal: [Feature Name]

## 1. Concept Summary
*One sentence describing the core value and the "Vibe" of the interface.*
**(e.g., "A mission control center for Sales Agents that feels like a Bloomberg terminal but simple.")**

## 2. The User Journey (Job-to-be-Done)
1.  User enters...
2.  User sees...
3.  User acts by...

## 3. Proposed Layout (Bento Grid)
We will use a [X]x[Y] grid structure.

| Slot | Component | Content/Function |
| :--- | :--- | :--- |
| Top-Left (2x1) | `MainChart` | Revenue over time. |
| Top-Right (1x1) | `ActionPanel` | Quick buttons (Call, Email). |
| Bottom (3x2) | `DataTable` | List of leads with inline editing. |

## 4. Interaction Patterns
- **Hover**: Cards lift up and reveal "Edit" actions.
- **Click**: Opens a `Sheet` (Side Panel) to preserve context.
- **Loading**: Optimistic updates with Skeleton UI.

## 5. Technical Implementation
- **Components**: `card`, `sheet`, `table`.
- **State**: `useQuery` for data, local state for UI interactions.
- **Constraints**: Mobile will stack these vertically.
