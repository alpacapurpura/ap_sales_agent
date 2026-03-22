export interface SalesMetrics {
  totalSales: number;
  salesChange: number; // percentage
  appointments: number;
  appointmentsChange: number; // percentage
  conversionRate: number; // percentage
  conversionChange: number; // percentage
  activeLeads: number;
}

export interface PaymentGatewayConfig {
  provider: 'culqi' | 'mercadopago';
  mode: 'sandbox' | 'production';
  sandboxKeys: {
    publicKey: string;
    secretKey: string;
  };
  productionKeys: {
    publicKey: string;
    secretKey: string;
  };
  isEnabled: boolean;
}

export interface SalesConversation {
  id: string;
  leadName: string;
  leadAvatar?: string;
  lastMessage: string;
  timestamp: string;
  unreadCount: number;
  status: 'active' | 'closed' | 'pending';
  platform: 'whatsapp' | 'instagram' | 'messenger';
}

export interface Appointment {
  id: string;
  title: string;
  start: string; // ISO date string
  end: string; // ISO date string
  attendees: string[];
  status: 'confirmed' | 'pending' | 'cancelled' | 'completed';
  meetLink?: string;
}

export interface SalesDashboardState {
  metrics: SalesMetrics;
  recentActivity: any[]; // To be defined
  upcomingAppointments: Appointment[];
}
