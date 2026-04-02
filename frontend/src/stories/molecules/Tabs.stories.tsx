import type { Meta, StoryObj } from '@storybook/nextjs-vite';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

const meta = {
  title: 'Molecules/Tabs',
  component: Tabs,
  tags: ['autodocs'],
} satisfies Meta<typeof Tabs>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Tabs defaultValue="tab1" className="w-[400px]">
      <TabsList>
        <TabsTrigger value="tab1">Account</TabsTrigger>
        <TabsTrigger value="tab2">Password</TabsTrigger>
        <TabsTrigger value="tab3">Settings</TabsTrigger>
      </TabsList>
      <TabsContent value="tab1">
        <p className="text-sm text-muted-foreground p-4">
          Make changes to your account here.
        </p>
      </TabsContent>
      <TabsContent value="tab2">
        <p className="text-sm text-muted-foreground p-4">
          Change your password here.
        </p>
      </TabsContent>
      <TabsContent value="tab3">
        <p className="text-sm text-muted-foreground p-4">
          Manage your settings here.
        </p>
      </TabsContent>
    </Tabs>
  ),
};
