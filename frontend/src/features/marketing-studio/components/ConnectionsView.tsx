import { PlugZap, Link, CheckCircle, AlertTriangle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

interface ConnectorStatus {
  id: string;
  name: string;
  type: 'CRM' | 'Ads' | 'Social' | 'Analytics';
  status: 'connected' | 'error' | 'disconnected';
  lastSync: string;
  icon: any;
}

const CONNECTORS: ConnectorStatus[] = [
  {
    id: 'hubspot',
    name: 'HubSpot',
    type: 'CRM',
    status: 'connected',
    lastSync: '2 min ago',
    icon: Link,
  },
  {
    id: 'meta_ads',
    name: 'Meta Ads',
    type: 'Ads',
    status: 'error',
    lastSync: '1 hour ago',
    icon: PlugZap,
  },
  {
    id: 'ga4',
    name: 'Google Analytics 4',
    type: 'Analytics',
    status: 'connected',
    lastSync: '5 min ago',
    icon: Link,
  },
  {
    id: 'linkedin',
    name: 'LinkedIn',
    type: 'Social',
    status: 'disconnected',
    lastSync: 'Never',
    icon: PlugZap,
  },
];

export default function ConnectionsView() {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Data Connectors</h2>
          <p className="text-muted-foreground">Manage your integrations and data sources.</p>
        </div>
        <Button>
          <PlugZap className="mr-2 h-4 w-4" /> Add New Connection
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {CONNECTORS.map((connector) => (
          <Card key={connector.id}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {connector.name}
              </CardTitle>
              <connector.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-2 mt-2">
                {connector.status === 'connected' && (
                  <Badge variant="default" className="bg-green-500 hover:bg-green-600">
                    <CheckCircle className="mr-1 h-3 w-3" /> Connected
                  </Badge>
                )}
                {connector.status === 'error' && (
                  <Badge variant="destructive">
                    <AlertTriangle className="mr-1 h-3 w-3" /> Error
                  </Badge>
                )}
                {connector.status === 'disconnected' && (
                  <Badge variant="secondary">Disconnected</Badge>
                )}
              </div>
              <p className="text-xs text-muted-foreground mt-4">
                Last sync: {connector.lastSync}
              </p>
              <div className="mt-4 flex justify-end">
                <Button variant="outline" size="sm">Configure</Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
