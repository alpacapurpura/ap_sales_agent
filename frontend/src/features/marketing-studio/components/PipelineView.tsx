import { ArrowRight, Layers, UserPlus, Zap } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface PipelineStage {
  id: string;
  name: string;
  count: number;
  color: string;
  icon: any;
}

const STAGES: PipelineStage[] = [
  { id: 'lead', name: 'Leads', count: 145, color: 'bg-blue-500', icon: UserPlus },
  { id: 'onboarding', name: 'Onboarding', count: 42, color: 'bg-yellow-500', icon: ArrowRight },
  { id: 'active', name: 'Active', count: 890, color: 'bg-green-500', icon: Zap },
  { id: 'churned', name: 'Churned', count: 23, color: 'bg-red-500', icon: Layers },
];

export default function PipelineView() {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Lifecycle Pipeline</h2>
          <p className="text-muted-foreground">Track user movement across lifecycle stages.</p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        {STAGES.map((stage) => (
          <Card key={stage.id} className="relative overflow-hidden">
            <div className={cn("absolute top-0 left-0 w-1 h-full", stage.color)} />
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {stage.name}
              </CardTitle>
              <stage.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stage.count}</div>
              <p className="text-xs text-muted-foreground">
                +12% from last month
              </p>
              <div className="mt-4 flex space-x-2">
                <Badge variant="outline" className="text-xs">
                  View Details
                </Badge>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Placeholder for detailed list or kanban */}
      <div className="rounded-md border p-8 text-center text-muted-foreground bg-muted/20">
        <Layers className="mx-auto h-12 w-12 opacity-20 mb-4" />
        <p>Select a stage to view detailed customer lists and actions.</p>
      </div>
    </div>
  );
}
