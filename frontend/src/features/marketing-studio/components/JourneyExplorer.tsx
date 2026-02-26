import { Activity, Calendar, User, ShoppingCart, Mail } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';

interface JourneyEvent {
  id: string;
  type: 'purchase' | 'email' | 'visit' | 'support';
  user: string;
  action: string;
  timestamp: string;
  amount?: string;
}

const EVENTS: JourneyEvent[] = [
  { id: '1', type: 'purchase', user: 'Ana G.', action: 'Purchased Premium Plan', timestamp: '2 mins ago', amount: '$499' },
  { id: '2', type: 'email', user: 'Carlos R.', action: 'Opened "Welcome" email', timestamp: '15 mins ago' },
  { id: '3', type: 'visit', user: 'Elena T.', action: 'Viewed Pricing Page', timestamp: '1 hour ago' },
  { id: '4', type: 'support', user: 'David L.', action: 'Opened ticket #1234', timestamp: '2 hours ago' },
  { id: '5', type: 'purchase', user: 'Sofia M.', action: 'Renewed Subscription', timestamp: '3 hours ago', amount: '$199' },
];

export default function JourneyExplorer() {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Customer Journey</h2>
          <p className="text-muted-foreground">Real-time event stream and user interactions.</p>
        </div>
        <Button variant="outline">
          <Calendar className="mr-2 h-4 w-4" /> Filter by Date
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>Latest 50 events across all channels.</CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[400px]">
              <div className="space-y-8">
                {EVENTS.map((event) => (
                  <div key={event.id} className="flex items-center">
                    <Avatar className="h-9 w-9">
                      <AvatarImage src={`https://avatar.vercel.sh/${event.user}.png`} alt={event.user} />
                      <AvatarFallback>{event.user.substring(0, 2)}</AvatarFallback>
                    </Avatar>
                    <div className="ml-4 space-y-1">
                      <p className="text-sm font-medium leading-none">{event.user}</p>
                      <p className="text-sm text-muted-foreground">
                        {event.action}
                      </p>
                    </div>
                    <div className="ml-auto font-medium">
                      {event.amount && <span className="text-green-600 mr-2">{event.amount}</span>}
                      <span className="text-xs text-muted-foreground">{event.timestamp}</span>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Event Distribution</CardTitle>
            <CardDescription>Events by type (Last 24h)</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center">
                <ShoppingCart className="h-4 w-4 text-blue-500 mr-2" />
                <div className="flex-1 space-y-1">
                  <p className="text-sm font-medium leading-none">Purchases</p>
                  <div className="w-full bg-secondary h-2 rounded-full overflow-hidden">
                    <div className="bg-blue-500 h-full w-[45%]" />
                  </div>
                </div>
                <div className="font-medium text-sm ml-4">45%</div>
              </div>
              <div className="flex items-center">
                <Mail className="h-4 w-4 text-yellow-500 mr-2" />
                <div className="flex-1 space-y-1">
                  <p className="text-sm font-medium leading-none">Emails</p>
                  <div className="w-full bg-secondary h-2 rounded-full overflow-hidden">
                    <div className="bg-yellow-500 h-full w-[30%]" />
                  </div>
                </div>
                <div className="font-medium text-sm ml-4">30%</div>
              </div>
              <div className="flex items-center">
                <Activity className="h-4 w-4 text-green-500 mr-2" />
                <div className="flex-1 space-y-1">
                  <p className="text-sm font-medium leading-none">Site Visits</p>
                  <div className="w-full bg-secondary h-2 rounded-full overflow-hidden">
                    <div className="bg-green-500 h-full w-[25%]" />
                  </div>
                </div>
                <div className="font-medium text-sm ml-4">25%</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
