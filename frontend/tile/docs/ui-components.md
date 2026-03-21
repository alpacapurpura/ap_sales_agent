# UI Components

All UI components are located in `src/components/ui/` and follow the shadcn/ui pattern: Radix UI primitives with Tailwind CSS styling. Import each component from its own file path.

## Capabilities

### Button

General-purpose interactive button supporting multiple visual variants and sizes.

```typescript { .api }
import { Button, buttonVariants, type ButtonProps } from "@/components/ui/button";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link";
  size?: "default" | "sm" | "lg" | "icon";
  asChild?: boolean; // render as child element via Radix Slot
}

function buttonVariants(props: { variant?: ButtonProps["variant"]; size?: ButtonProps["size"]; className?: string }): string;
```

**Usage:**
```typescript
<Button variant="outline" size="sm" onClick={handleClick}>Save</Button>
<Button asChild><a href="/home">Go Home</a></Button>
```

### Input

Standard text input field.

```typescript { .api }
import { Input } from "@/components/ui/input";
// Accepts all standard HTML <input> attributes
```

### Textarea

Multi-line text input.

```typescript { .api }
import { Textarea } from "@/components/ui/textarea";
// Accepts all standard HTML <textarea> attributes
```

### Label

Accessible form label.

```typescript { .api }
import { Label, labelVariants } from "@/components/ui/label";
// Accepts all standard HTML <label> attributes + className
```

### Form (React Hook Form Integration)

Complete form system integrated with React Hook Form and Zod validation.

```typescript { .api }
import {
  Form,
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormDescription,
  FormMessage,
  useFormField,
} from "@/components/ui/form";

// useFormField returns context for current field
function useFormField(): {
  id: string;
  name: string;
  formItemId: string;
  formDescriptionId: string;
  formMessageId: string;
  invalid: boolean;
  isDirty: boolean;
  isTouched: boolean;
  isValidating: boolean;
  error?: FieldError;
}
```

**Usage:**
```typescript
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod/v4";

const schema = z.object({ name: z.string().min(2) });

function MyForm() {
  const form = useForm({ resolver: zodResolver(schema) });
  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)}>
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Name</FormLabel>
              <FormControl><Input {...field} /></FormControl>
              <FormDescription>Enter your full name.</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
        <Button type="submit">Submit</Button>
      </form>
    </Form>
  );
}
```

### Checkbox

Binary checkbox input.

```typescript { .api }
import { Checkbox } from "@/components/ui/checkbox";
// Props: checked, onCheckedChange, disabled, id, className
// onCheckedChange: (checked: boolean | 'indeterminate') => void
```

### RadioGroup

Radio button group for single selection.

```typescript { .api }
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
// RadioGroup props: value, onValueChange, defaultValue, disabled
// RadioGroupItem props: value (required), id, disabled
```

### Switch

Toggle switch control.

```typescript { .api }
import { Switch } from "@/components/ui/switch";
// Props: checked, onCheckedChange, disabled, id, className
```

### Select

Dropdown select with customizable items.

```typescript { .api }
import {
  Select,
  SelectGroup,
  SelectValue,
  SelectTrigger,
  SelectContent,
  SelectLabel,
  SelectItem,
  SelectSeparator,
  SelectScrollUpButton,
  SelectScrollDownButton,
} from "@/components/ui/select";
// Select props: value, onValueChange, defaultValue, open, onOpenChange, disabled
```

**Usage:**
```typescript
<Select value={value} onValueChange={setValue}>
  <SelectTrigger><SelectValue placeholder="Select..." /></SelectTrigger>
  <SelectContent>
    <SelectItem value="a">Option A</SelectItem>
    <SelectItem value="b">Option B</SelectItem>
  </SelectContent>
</Select>
```

### RichSelect

Enhanced select with labels and optional descriptions per option.

```typescript { .api }
import { RichSelect, type RichSelectOption } from "@/components/ui/rich-select";

interface RichSelectOption {
  value: string;
  label: string;
  description?: string;
}

function RichSelect(props: {
  value?: string;
  onChange: (value: string) => void;
  options: RichSelectOption[];
  placeholder?: string;
  className?: string;
}): JSX.Element;
```

### CurrencySelector

Specialized select for picking from supported currencies.

```typescript { .api }
import { CurrencySelector } from "@/components/ui/currency-selector";

function CurrencySelector(props: {
  value?: string;       // currency code e.g. "USD"
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
}): JSX.Element;
```

### TimezoneSelect

Timezone picker component.

```typescript { .api }
import { TimezoneSelect } from "@/components/ui/timezone-select";

function TimezoneSelect(props: {
  value?: string;       // IANA timezone e.g. "America/New_York"
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
}): JSX.Element;
```

### SmartDateTimePicker

Timezone-aware date and time picker.

```typescript { .api }
import { SmartDateTimePicker } from "@/components/ui/smart-datetime-picker";

function SmartDateTimePicker(props: {
  value?: Date;
  onChange: (date: Date | undefined) => void;
  timezone?: string;  // IANA timezone
  className?: string;
}): JSX.Element;
```

### Calendar

Full calendar date picker using react-day-picker.

```typescript { .api }
import { Calendar, CalendarDayButton } from "@/components/ui/calendar";
// Calendar accepts all react-day-picker DayPicker props
// Common props: mode, selected, onSelect, disabled, className
```

### Dialog

Modal dialog overlay.

```typescript { .api }
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
  DialogClose,
  DialogPortal,
  DialogOverlay,
} from "@/components/ui/dialog";
// Dialog props: open, onOpenChange, defaultOpen, modal
```

**Usage:**
```typescript
<Dialog open={open} onOpenChange={setOpen}>
  <DialogTrigger asChild><Button>Open</Button></DialogTrigger>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Confirm Action</DialogTitle>
      <DialogDescription>Are you sure?</DialogDescription>
    </DialogHeader>
    <DialogFooter>
      <DialogClose asChild><Button variant="outline">Cancel</Button></DialogClose>
      <Button onClick={handleConfirm}>Confirm</Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

### AlertDialog

Accessible confirmation dialog (blocks interaction until resolved).

```typescript { .api }
import {
  AlertDialog,
  AlertDialogTrigger,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogFooter,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogPortal,
  AlertDialogOverlay,
} from "@/components/ui/alert-dialog";
```

### Sheet

Side panel (drawer) sliding from screen edges.

```typescript { .api }
import {
  Sheet,
  SheetTrigger,
  SheetContent,
  SheetHeader,
  SheetFooter,
  SheetTitle,
  SheetDescription,
  SheetClose,
  SheetPortal,
  SheetOverlay,
} from "@/components/ui/sheet";
// SheetContent props: side?: "top" | "right" | "bottom" | "left" (default: "right")
```

### Popover

Floating content anchored to a trigger element.

```typescript { .api }
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover";
// Popover props: open, onOpenChange, defaultOpen
// PopoverContent props: side, align, sideOffset, className
```

### DropdownMenu

Contextual dropdown menu.

```typescript { .api }
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuCheckboxItem,
  DropdownMenuRadioItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuShortcut,
  DropdownMenuGroup,
  DropdownMenuPortal,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuRadioGroup,
} from "@/components/ui/dropdown-menu";
```

**Usage:**
```typescript
<DropdownMenu>
  <DropdownMenuTrigger asChild><Button variant="outline">Menu</Button></DropdownMenuTrigger>
  <DropdownMenuContent>
    <DropdownMenuLabel>Actions</DropdownMenuLabel>
    <DropdownMenuSeparator />
    <DropdownMenuItem onSelect={() => handleEdit()}>Edit</DropdownMenuItem>
    <DropdownMenuItem onSelect={() => handleDelete()} className="text-destructive">Delete</DropdownMenuItem>
  </DropdownMenuContent>
</DropdownMenu>
```

### Command

Command palette / combobox using cmdk.

```typescript { .api }
import {
  Command,
  CommandDialog,
  CommandInput,
  CommandList,
  CommandEmpty,
  CommandGroup,
  CommandItem,
  CommandSeparator,
  CommandShortcut,
} from "@/components/ui/command";
// CommandDialog wraps Command in a Dialog for global search palettes
```

### Tooltip

Floating tooltip on hover/focus.

```typescript { .api }
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
  TooltipProvider,
} from "@/components/ui/tooltip";
// TooltipProvider: place at app root (wraps with delay context)
// TooltipContent props: side, align, sideOffset, className
```

**Usage:**
```typescript
<TooltipProvider>
  <Tooltip>
    <TooltipTrigger asChild><Button>Hover me</Button></TooltipTrigger>
    <TooltipContent>This is a tooltip</TooltipContent>
  </Tooltip>
</TooltipProvider>
```

### Accordion

Collapsible content sections.

```typescript { .api }
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from "@/components/ui/accordion";
// Accordion props: type ("single" | "multiple"), collapsible, defaultValue, value, onValueChange
```

### Collapsible

Simple show/hide content toggle.

```typescript { .api }
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from "@/components/ui/collapsible";
// Collapsible props: open, onOpenChange, defaultOpen, disabled
```

### Tabs

Tabbed navigation with content panels.

```typescript { .api }
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
// Tabs props: value, onValueChange, defaultValue, orientation
// TabsContent props: value (required)
```

### Card

Content card container with optional sections.

```typescript { .api }
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
```

### Badge

Inline status or label badge.

```typescript { .api }
import { Badge, badgeVariants, type BadgeProps } from "@/components/ui/badge";

interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary" | "destructive" | "outline";
}
```

### Alert

Inline notification or alert banner.

```typescript { .api }
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
// Alert props: variant?: "default" | "destructive"
```

### Avatar

User avatar with image and fallback text.

```typescript { .api }
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
// AvatarImage props: src, alt
// AvatarFallback: text content shown when image fails/loads
```

### Table

Data table layout components.

```typescript { .api }
import {
  Table,
  TableHeader,
  TableBody,
  TableFooter,
  TableHead,
  TableRow,
  TableCell,
  TableCaption,
} from "@/components/ui/table";
```

### ScrollArea

Custom styled scrollable container.

```typescript { .api }
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
// ScrollArea props: className, style, type ("auto" | "always" | "scroll" | "hover")
// ScrollBar props: orientation ("vertical" | "horizontal")
```

### Separator

Visual divider line.

```typescript { .api }
import { Separator } from "@/components/ui/separator";
// Props: orientation?: "horizontal" | "vertical"; decorative?: boolean
```

### Progress

Linear progress bar.

```typescript { .api }
import { Progress } from "@/components/ui/progress";
// Props: value?: number (0-100); className
```

### Skeleton

Loading placeholder with shimmer animation.

```typescript { .api }
import { Skeleton } from "@/components/ui/skeleton";
// Props: className (controls size/shape)
```

### Toaster (Toast Notifications)

Global toast notification system using sonner library. Place once in the root layout.

```typescript { .api }
import { Toaster } from "@/components/ui/sonner";
// Import toast trigger from sonner directly:
import { toast } from "sonner";

// Usage:
toast("Message"); // simple
toast.success("Saved!"); // success
toast.error("Failed!"); // error
toast.warning("Warning"); // warning
toast.promise(promise, { loading: "...", success: "Done", error: "Error" });
```

```typescript
// In root layout:
<Toaster />
```

### HighlightedText

Highlights matching query text within a string.

```typescript { .api }
import { HighlightedText } from "@/components/ui/highlighted-text";

function HighlightedText(props: {
  text: string;
  query: string;
  className?: string;
}): JSX.Element;
```

### FieldInfo

Info icon that shows a tooltip label on hover.

```typescript { .api }
import { FieldInfo } from "@/components/ui/field-info";

function FieldInfo(props: {
  label: string;
  className?: string;
}): JSX.Element;
```
