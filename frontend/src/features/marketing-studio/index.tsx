import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import ConnectionsView from './components/ConnectionsView';
import PipelineView from './components/PipelineView';
import JourneyExplorer from './components/JourneyExplorer';
import GrowthDashboard from './components/GrowthDashboard';

export default function MarketingStudio() {
  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Growth Studio</h2>
      </div>
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Growth Dashboard</TabsTrigger>
          <TabsTrigger value="pipeline">Lifecycle Pipeline</TabsTrigger>
          <TabsTrigger value="journey">Journey Explorer</TabsTrigger>
          <TabsTrigger value="connections">Connections</TabsTrigger>
        </TabsList>
        <TabsContent value="overview" className="space-y-4">
          <GrowthDashboard />
        </TabsContent>
        <TabsContent value="pipeline" className="space-y-4">
          <PipelineView />
        </TabsContent>
        <TabsContent value="journey" className="space-y-4">
          <JourneyExplorer />
        </TabsContent>
        <TabsContent value="connections" className="space-y-4">
          <ConnectionsView />
        </TabsContent>
      </Tabs>
    </div>
  );
}
