"use client";

import { useState } from "react";
import { useAuditUsers } from "@/lib/api/audit";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";
import { formatDistanceToNow } from "date-fns";
import { es } from "date-fns/locale";

interface UserListProps {
  selectedUserId: string | null;
  onSelectUser: (userId: string) => void;
}

export function UserList({ selectedUserId, onSelectUser }: UserListProps) {
  const { data: users, isLoading } = useAuditUsers();
  const [search, setSearch] = useState("");

  const filteredUsers = users?.filter((u) =>
    (u.user.full_name || "").toLowerCase().includes(search.toLowerCase()) ||
    (u.user.telegram_id || "").includes(search) ||
    (u.user.whatsapp_id || "").includes(search)
  );

  return (
    <Card className="h-full flex flex-col border-r rounded-none border-y-0 border-l-0">
      <CardHeader className="p-4 border-b">
        <CardTitle className="text-lg">Usuarios</CardTitle>
        <Input
          placeholder="Buscar..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="mt-2"
        />
      </CardHeader>
      <ScrollArea className="flex-1">
        <div className="p-2 space-y-2">
          {isLoading && <div className="p-4 text-center text-muted-foreground">Cargando...</div>}
          {filteredUsers?.map((item) => (
            <div
              key={item.user.id}
              onClick={() => onSelectUser(item.user.id)}
              className={cn(
                "p-3 rounded-lg cursor-pointer transition-colors flex items-center gap-3 hover:bg-muted",
                selectedUserId === item.user.id ? "bg-muted" : "bg-transparent"
              )}
            >
              <Avatar className="h-10 w-10">
                <AvatarFallback>{(item.user.full_name || "??").substring(0, 2).toUpperCase()}</AvatarFallback>
              </Avatar>
              <div className="flex-1 overflow-hidden">
                <div className="font-medium truncate">{item.user.full_name || "Sin Nombre"}</div>
                <div className="text-xs text-muted-foreground flex justify-between">
                  <span>
                    {item.user.telegram_id ? "Telegram" : item.user.whatsapp_id ? "WhatsApp" : "Web"}
                  </span>
                  <span>
                    {item.last_activity && formatDistanceToNow(new Date(item.last_activity), { addSuffix: true, locale: es })}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>
    </Card>
  );
}
