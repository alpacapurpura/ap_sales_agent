"use client";
import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { crmDashboardApi, TickerItem } from "@/lib/api/crm-dashboard-api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { TrendingUp, DollarSign, Loader2 } from "lucide-react";
import { format, parseISO } from "date-fns";

export const SalesLane = () => {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const [sales, setSales] = useState<TickerItem[]>([]);
  const [range, setRange] = useState<"30d" | "today" | "week" | "all">("30d");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      if (!isLoaded || !isSignedIn) return;

      setLoading(true);
      try {
        const token = await getToken();
        if (!token) return;
        console.log("Fetching ticker...", range);
        const data = await crmDashboardApi.getTicker(token, range);
        console.log("Ticker data:", data);
        setSales(data);
      } catch (error) {
        console.error("Failed to fetch ticker", error);
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, [getToken, isLoaded, isSignedIn, range]);

  const totalRevenue = sales.reduce((sum, sale) => sum + sale.amount, 0);

  return (
    <Card className="flex flex-col h-full bg-slate-50/50 dark:bg-slate-900/20 border-l-4 border-l-green-500">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-bold text-green-700 dark:text-green-500 flex items-center gap-2">
            <span>Crecimiento & LTV</span>
            <TrendingUp className="w-5 h-5" />
          </CardTitle>
          <div className="flex bg-muted rounded-lg p-1">
            <Button
              variant={range === "today" ? "secondary" : "ghost"}
              size="sm"
              className="h-6 text-xs"
              onClick={() => setRange("today")}
            >
              Today
            </Button>
            <Button
              variant={range === "30d" ? "secondary" : "ghost"}
              size="sm"
              className="h-6 text-xs"
              onClick={() => setRange("30d")}
            >
              30D
            </Button>
          </div>
        </div>
        <div className="flex justify-between items-baseline mt-2">
          <p className="text-xs text-muted-foreground">Revenue Ticker</p>
          <span className="text-xl font-bold text-green-600 dark:text-green-400">
            ${totalRevenue.toLocaleString()}
          </span>
        </div>
      </CardHeader>
      <CardContent className="flex-1 p-0">
        <ScrollArea className="h-[500px] px-4">
          <div className="space-y-3 py-4">
            {sales.map((sale) => (
              <div
                key={sale.id}
                className="p-3 bg-white dark:bg-slate-950 rounded-lg border shadow-sm flex justify-between items-center"
              >
                <div>
                  <div className="font-semibold text-sm flex items-center gap-2">
                    <DollarSign className="w-4 h-4 text-green-500" />
                    <span>${sale.amount.toLocaleString()}</span>
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {sale.customer_name || "Unknown Customer"}
                  </div>
                  <div className="text-[10px] text-muted-foreground">
                    {format(parseISO(sale.occurred_at), "MMM d, h:mm a")}
                  </div>
                </div>
                <div className="text-right">
                  <Badge
                    variant={sale.stage === "EXPANSION" ? "default" : "outline"}
                    className="text-[10px] mb-1 block w-fit ml-auto"
                  >
                    {sale.stage}
                  </Badge>
                  <div
                    className="text-[10px] text-muted-foreground truncate max-w-[100px]"
                    title={sale.offer_name || ""}
                  >
                    {sale.offer_name}
                  </div>
                </div>
              </div>
            ))}
            {!loading && sales.length === 0 && (
              <div className="text-center text-sm text-muted-foreground py-10">
                No sales recorded
              </div>
            )}
            {loading && (
              <div className="flex justify-center items-center py-10">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
};
