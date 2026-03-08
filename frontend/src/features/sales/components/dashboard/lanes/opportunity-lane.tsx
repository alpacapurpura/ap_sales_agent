"use client";
import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { crmDashboardApi, PipelineItem } from "@/lib/api/crm-dashboard-api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MessageCircle, Flame, Loader2 } from "lucide-react";

export const OpportunityLane = () => {
    const { getToken, isLoaded, isSignedIn } = useAuth();
    const [leads, setLeads] = useState<PipelineItem[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetch = async () => {
            if (!isLoaded || !isSignedIn) return;
            
            try {
                const token = await getToken();
                if (!token) return;
                console.log("Fetching pipeline...");
                const data = await crmDashboardApi.getPipeline(token);
                console.log("Pipeline data:", data);
                setLeads(data);
            } catch (error) {
                console.error("Failed to fetch pipeline", error);
            } finally {
                setLoading(false);
            }
        };
        fetch();
    }, [getToken, isLoaded, isSignedIn]);

    return (
        <Card className="flex flex-col h-full bg-slate-50/50 dark:bg-slate-900/20 border-l-4 border-l-amber-500">
            <CardHeader className="pb-2">
                <CardTitle className="flex items-center justify-between text-lg font-bold text-amber-700 dark:text-amber-500">
                    <span>Nutrición & Oportunidad</span>
                    <Flame className="w-5 h-5" />
                </CardTitle>
                <p className="text-xs text-muted-foreground">High Intent Leads (MQLs)</p>
            </CardHeader>
            <CardContent className="flex-1 p-0">
                <ScrollArea className="h-[500px] px-4">
                    <div className="space-y-3 py-4">
                        {leads.map(lead => (
                            <div key={lead.id} className="p-3 bg-white dark:bg-slate-950 rounded-lg border shadow-sm flex justify-between items-start">
                                <div>
                                    <div className="font-semibold text-sm">{lead.full_name || "Unknown"}</div>
                                    <div className="text-xs text-muted-foreground mt-1 flex gap-2">
                                        <Badge variant="outline" className={lead.intent_score > 80 ? "border-red-500 text-red-500" : "border-amber-500 text-amber-500"}>
                                            Score: {lead.intent_score}
                                        </Badge>
                                        <span className="capitalize">{lead.temperature?.toLowerCase()}</span>
                                    </div>
                                </div>
                                <Button size="icon" variant="ghost" className="h-8 w-8 text-blue-500">
                                    <MessageCircle className="w-4 h-4" />
                                </Button>
                            </div>
                        ))}
                        {!loading && leads.length === 0 && (
                            <div className="text-center text-sm text-muted-foreground py-10">No hot leads found</div>
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
}
