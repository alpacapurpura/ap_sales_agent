I will wrap the "Reservas" tab content in a `Card` structure to match the style of other tabs.

**Step 1: Update SalesContent Component**

* Locate the `TabsContent` with `value="reservations"`.

* Wrap the existing `Tabs` (the nested horizontal tabs) inside a `Card` component.

* Add a `CardHeader` with:

  * `CardTitle`: "Reservas" with the `CalendarDays` icon.

  * `CardDescription`: "Gestiona tus citas y reservas agendadas."

* Wrap the existing nested `Tabs` inside `CardContent`.

* Ensure proper nesting:

  ```tsx
  <TabsContent value="reservations" className="mt-0">
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CalendarDays className="h-6 w-6" />
          Reservas
        </CardTitle>
        <CardDescription>Gestiona tus citas y reservas agendadas.</CardDescription>
      </CardHeader>
      <CardContent>
         {/* Existing Nested Tabs */}
      </CardContent>
    </Card>
  </TabsContent>
  ```

**Step 2: Verify Layout**

* This will ensure the "Reservas" section has the same white background container, title header, and border as the "PlaceholderContent" used in other tabs.

