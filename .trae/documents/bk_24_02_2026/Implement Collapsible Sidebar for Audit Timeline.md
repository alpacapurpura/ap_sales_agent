# Implement Collapsible Sidebar for Audit Timeline

I will make the Lead List sidebar in the Audit page collapsible to provide more space for the conversation timeline.

## 1. Modify `LeadList` Component
File: `frontend/src/features/audit/components/user-list.tsx`

- **Props Update**: Add `isCollapsed: boolean` and `onToggle: () => void`.
- **UI Logic**:
  - **Expanded Mode (`w-80`)**:
    - Show existing Search Bar and Title.
    - Add a "Collapse" button (icon: `PanelLeftClose`) in the header.
    - Show full lead details (Avatar + Name + Info).
  - **Collapsed Mode (`w-20`)**:
    - Hide Title and Search Bar.
    - Show an "Expand" button (icon: `PanelLeftOpen`) at the top, centered.
    - Show only Avatars in the list, centered.
    - Add `Tooltip` to Avatars to show the lead's name on hover.
- **Imports**: Add `Button`, `Tooltip`, and Lucide icons (`PanelLeftClose`, `PanelLeftOpen`).

## 2. Update `AuditPage` Layout
File: `frontend/src/app/(dashboard)/audit/page.tsx`

- **State Management**: Add `const [isCollapsed, setIsCollapsed] = useState(false)`.
- **Layout Adjustments**:
  - Pass `isCollapsed` and `onToggle={() => setIsCollapsed(!isCollapsed)}` to `LeadList`.
  - Apply dynamic width class to the sidebar container:
    - `w-80` when expanded.
    - `w-20` (approx 80px) when collapsed.
  - Add `transition-all duration-300 ease-in-out` for smooth animation.

## Verification
- Verify that clicking the toggle button smoothly resizes the sidebar.
- Ensure the lead list content adapts correctly (hiding text, showing tooltips).
- Confirm that selecting a lead still works in collapsed mode.
