import type { Meta, StoryObj } from '@storybook/nextjs-vite';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';

const meta = {
  title: 'Organisms/DataTable',
  component: Table,
  tags: ['autodocs'],
} satisfies Meta<typeof Table>;

export default meta;
type Story = StoryObj<typeof meta>;

const data = [
  { name: 'Ana Garcia', status: 'Active', email: 'ana@example.com' },
  { name: 'Carlos Lopez', status: 'Inactive', email: 'carlos@example.com' },
  { name: 'Maria Rodriguez', status: 'Active', email: 'maria@example.com' },
  { name: 'Juan Martinez', status: 'Pending', email: 'juan@example.com' },
  { name: 'Sofia Hernandez', status: 'Active', email: 'sofia@example.com' },
];

const statusVariant = (status: string) => {
  switch (status) {
    case 'Active': return 'default' as const;
    case 'Inactive': return 'destructive' as const;
    default: return 'secondary' as const;
  }
};

export const Default: Story = {
  render: () => (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Email</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map((row) => (
          <TableRow key={row.email}>
            <TableCell className="font-medium">{row.name}</TableCell>
            <TableCell>
              <Badge variant={statusVariant(row.status)}>{row.status}</Badge>
            </TableCell>
            <TableCell>{row.email}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  ),
};
