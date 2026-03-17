"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import { KeyFigure } from "@/features/brand/types";
import { brandApi } from "@/features/brand/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Loader2, Users } from "lucide-react";
import { toast } from "sonner";
import { ScrollArea } from "@/components/ui/scroll-area";

interface InstructorsWidgetProps {
    selectedInstructorIds: string[];
}

export function InstructorsWidget({ selectedInstructorIds }: InstructorsWidgetProps) {
    const { getToken } = useAuth();
    const [team, setTeam] = useState<KeyFigure[]>([]);
    const [loading, setLoading] = useState(false);

    // Fetch Team Data
    const fetchTeam = async () => {
        setLoading(true);
        try {
            const token = await getToken();
            if (!token) return;
            const settings = await brandApi.getBrandSettings(token);
            setTeam(settings.team || []);
        } catch (error) {
            console.error("Error fetching team:", error);
            // Silent error in read-only widget
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTeam();
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    const selectedInstructors = team.filter(m => selectedInstructorIds.includes(m.id));

    if (selectedInstructors.length === 0) return null;

    return (
        <Card className="border-slate-200 dark:border-slate-800 mb-6 bg-slate-50/50 dark:bg-slate-900/20">
            <CardHeader className="pb-2 pt-4">
                <CardTitle className="text-xs font-semibold flex items-center gap-2 uppercase tracking-wider text-muted-foreground">
                    <Users className="w-3 h-3" />
                    Autoridad / Mentores
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="flex flex-col gap-3">
                    {loading ? (
                         <div className="flex justify-center py-2"><Loader2 className="animate-spin w-4 h-4 text-muted-foreground" /></div>
                    ) : (
                        selectedInstructors.map(instructor => (
                            <div key={instructor.id} className="flex items-center gap-3">
                                <Avatar className="h-8 w-8 border shadow-sm">
                                    <AvatarImage src={instructor.headshot_url} className="object-cover" />
                                    <AvatarFallback>{instructor.name.substring(0,2).toUpperCase()}</AvatarFallback>
                                </Avatar>
                                <div className="grid gap-0.5">
                                    <span className="text-sm font-medium leading-none">{instructor.name}</span>
                                    <span className="text-[10px] text-muted-foreground line-clamp-1">{instructor.role}</span>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </CardContent>
        </Card>
    );
}
