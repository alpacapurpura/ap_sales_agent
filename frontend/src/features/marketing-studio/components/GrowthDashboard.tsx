"use client";

import { TrendingUp, Users, DollarSign, Activity } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useMarketingData } from '../hooks/useMarketingData';

export default function GrowthDashboard() {
  const { rfm, loading } = useMarketingData();

  const formatCurrency = (val: number) => 
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);

  if (loading) {
    return <div className="p-8 text-center text-muted-foreground">Loading dashboard data...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Growth & Retention</h2>
          <p className="text-muted-foreground">Key performance indicators for customer retention and value.</p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Total Revenue
            </CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(0)}</div>
            <p className="text-xs text-muted-foreground">
              0% from last month
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Active Users
            </CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{rfm?.totalCustomers || 0}</div>
            <p className="text-xs text-muted-foreground">
              {rfm ? `${rfm.activePercentage}% active` : '0% active'}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Churn Rate</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{rfm?.churnRate || 0}%</div>
            <p className="text-xs text-muted-foreground">
              0% from last month
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Avg. LTV
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(rfm?.averageLtv || 0)}</div>
            <p className="text-xs text-muted-foreground">
              0% from last month
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Revenue over time</CardTitle>
          </CardHeader>
          <CardContent className="pl-2">
            <div className="h-[200px] w-full flex items-center justify-center border border-dashed rounded-md">
               <p className="text-muted-foreground">No data available</p>
            </div>
          </CardContent>
        </Card>
        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Customer Segments</CardTitle>
          </CardHeader>
          <CardContent>
             <div className="h-[200px] flex items-center justify-center border border-dashed rounded-md">
                <p className="text-muted-foreground">No segments data</p>
             </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
