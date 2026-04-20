"use client";

import { cva } from "class-variance-authority";
import { formatDistanceToNow } from "date-fns";
import { es } from "date-fns/locale";
import { MessageSquare, Send, ChevronLeft, Search, MoreVertical, CheckCircle2 } from "lucide-react";
import { useState } from "react";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";

import type { SalesConversation } from "../../types/sales-studio";

// Mock Data removed

interface SalesInboxSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const messageVariants = cva("p-3 rounded-lg max-w-[80%] text-sm", {
  variants: {
    variant: {
      received: "bg-muted rounded-tl-none",
      sent: "bg-primary text-primary-foreground rounded-tr-none",
    },
  },
  defaultVariants: {
    variant: "received",
  },
});

const MessageBubble = ({
  variant,
  children,
}: {
  variant: "received" | "sent";
  children: React.ReactNode;
}) => (
  <div className={cn("flex", variant === "sent" ? "justify-end" : "justify-start")}>
    <div className={cn(messageVariants({ variant }))}>{children}</div>
  </div>
);

/**
 *
 */
export function SalesInboxSheet({ open, onOpenChange }: SalesInboxSheetProps) {
  const [selectedConversation, setSelectedConversation] = useState<SalesConversation | null>(null);
  const [replyText, setReplyText] = useState("");
  const conversations: SalesConversation[] = [];

  const handleSelect = (conversation: SalesConversation) => {
    setSelectedConversation(conversation);
  };

  const handleBack = () => {
    setSelectedConversation(null);
  };

  const handleSend = () => {
    if (!replyText.trim()) return;
    // Logic to send message would go here
    setReplyText("");
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-md p-0 flex flex-col h-full border-l">
        {!selectedConversation ? (
          // List View
          <div className="flex flex-col h-full">
            <SheetHeader className="px-6 py-4 border-b">
              <SheetTitle className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5" />
                Inbox de Ventas
              </SheetTitle>
              <SheetDescription>Gestiona tus conversaciones activas con leads.</SheetDescription>
              <div className="relative mt-2">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input placeholder="Buscar leads..." className="pl-9 bg-muted/50" />
              </div>
            </SheetHeader>

            <Tabs defaultValue="active" className="flex-1 flex flex-col">
              <div className="px-6 pt-2">
                <TabsList className="w-full grid grid-cols-2">
                  <TabsTrigger value="active">Activos</TabsTrigger>
                  <TabsTrigger value="closed">Cerrados</TabsTrigger>
                </TabsList>
              </div>

              <TabsContent value="active" className="flex-1 p-0 mt-2 h-full">
                <ScrollArea className="h-[calc(100vh-200px)]">
                  <div className="flex flex-col">
                    {conversations.filter((c) => c.status !== "closed").length > 0 ? (
                      conversations
                        .filter((c) => c.status !== "closed")
                        .map((conversation) => (
                          <ConversationItem
                            key={conversation.id}
                            conversation={conversation}
                            onClick={() => handleSelect(conversation)}
                          />
                        ))
                    ) : (
                      <div className="flex flex-col items-center justify-center h-40 text-muted-foreground">
                        <MessageSquare className="h-8 w-8 mb-2 opacity-50" />
                        <p className="text-sm">No hay conversaciones activas</p>
                      </div>
                    )}
                  </div>
                </ScrollArea>
              </TabsContent>

              <TabsContent value="closed" className="flex-1 p-0 mt-2 h-full">
                <ScrollArea className="h-[calc(100vh-200px)]">
                  <div className="flex flex-col">
                    {conversations.filter((c) => c.status === "closed").length > 0 ? (
                      conversations
                        .filter((c) => c.status === "closed")
                        .map((conversation) => (
                          <ConversationItem
                            key={conversation.id}
                            conversation={conversation}
                            onClick={() => handleSelect(conversation)}
                          />
                        ))
                    ) : (
                      <div className="flex flex-col items-center justify-center h-40 text-muted-foreground">
                        <CheckCircle2 className="h-8 w-8 mb-2 opacity-50" />
                        <p className="text-sm">No hay conversaciones cerradas</p>
                      </div>
                    )}
                  </div>
                </ScrollArea>
              </TabsContent>
            </Tabs>
          </div>
        ) : (
          // Chat View
          <div className="flex flex-col h-full bg-muted/10">
            <div className="flex items-center justify-between px-4 py-3 border-b bg-background">
              <div className="flex items-center gap-3">
                <Button variant="ghost" size="icon" onClick={handleBack} className="-ml-2">
                  <ChevronLeft className="h-5 w-5" />
                </Button>
                <div className="flex items-center gap-2">
                  <Avatar className="h-8 w-8">
                    <AvatarFallback>
                      {selectedConversation.leadName.substring(0, 2).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <h4 className="text-sm font-semibold">{selectedConversation.leadName}</h4>
                    <p className="text-xs text-muted-foreground capitalize">
                      {selectedConversation.platform}
                    </p>
                  </div>
                </div>
              </div>
              <Button variant="ghost" size="icon">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </div>

            <ScrollArea className="flex-1 p-4">
              <div className="space-y-4">{/* Messages would be mapped here */}</div>
            </ScrollArea>

            <div className="p-4 bg-background border-t">
              <div className="flex items-center gap-2">
                <Input
                  placeholder="Escribe una respuesta..."
                  value={replyText}
                  onChange={(e) => setReplyText(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSend()}
                />
                <Button size="icon" onClick={handleSend} disabled={!replyText.trim()}>
                  <Send className="h-4 w-4" />
                </Button>
              </div>
              <div className="flex justify-between items-center mt-2">
                <p className="text-xs text-muted-foreground">Presiona Enter para enviar</p>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 text-xs text-green-600 hover:text-green-700 hover:bg-green-50"
                >
                  <CheckCircle2 className="mr-1 h-3 w-3" /> Marcar resuelto
                </Button>
              </div>
            </div>
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}

function ConversationItem({
  conversation,
  onClick,
}: {
  conversation: SalesConversation;
  onClick: () => void;
}) {
  return (
    <div
      onClick={onClick}
      className="flex items-start gap-3 p-4 hover:bg-muted/50 cursor-pointer border-b transition-colors"
    >
      <div className="relative">
        <Avatar>
          <AvatarFallback>{conversation.leadName.substring(0, 2).toUpperCase()}</AvatarFallback>
        </Avatar>
        {conversation.platform === "whatsapp" && (
          <span className="absolute -bottom-1 -right-1 bg-green-500 rounded-full w-4 h-4 border-2 border-background flex items-center justify-center text-[8px] text-white">
            W
          </span>
        )}
      </div>
      <div className="flex-1 overflow-hidden">
        <div className="flex justify-between items-start mb-1">
          <span className="font-semibold text-sm truncate">{conversation.leadName}</span>
          <span className="text-xs text-muted-foreground whitespace-nowrap ml-2">
            {formatDistanceToNow(new Date(conversation.timestamp), { addSuffix: true, locale: es })}
          </span>
        </div>
        <p
          className={cn(
            "text-sm truncate",
            conversation.unreadCount > 0 ? "font-medium text-foreground" : "text-muted-foreground",
          )}
        >
          {conversation.lastMessage}
        </p>
      </div>
      {conversation.unreadCount > 0 && (
        <Badge
          variant="default"
          className="ml-2 h-5 w-5 flex items-center justify-center p-0 rounded-full text-[10px]"
        >
          {conversation.unreadCount}
        </Badge>
      )}
    </div>
  );
}
