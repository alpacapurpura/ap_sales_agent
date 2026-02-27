# Technical Constraints & Boundaries

## 1. Mobile Density (The "Phone" Bottleneck)
**Constraint**: Complex Dashboards (Bento Grids) do not fit on mobile screens.
**Rule**:
- **Desktop**: Grid Layout.
- **Mobile**: Linear Stack (Column).
- **Navigation**: Use `Tabs` or `Sheet` to access secondary panels on mobile. Do NOT try to squeeze 3 columns.

## 2. Async Latency (The "Waiting" Game)
**Constraint**: Backend/AI operations take 2-10 seconds.
**Rule**:
- **Never Block**: The UI must remain responsive.
- **Always Feedback**: Use `sonner` toasts ("Processing...") or `skeleton` loaders.
- **No "White Screen"**: Always render the container first, then load the data.

## 3. Shadcn Rigidity
**Constraint**: Shadcn components are designed to look "clean".
**Rule**:
- To be "Disruptive", you must override default styles.
- **Do**: Use custom borders, gradients, and typography sizes.
- **Don't**: Break accessibility (contrast, focus states).
