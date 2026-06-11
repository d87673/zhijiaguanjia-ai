// ─── User / Auth ───
export interface User {
  id: string;
  name: string | null;
  email: string;
  role: 'admin' | 'manager' | 'staff';
  phone: string | null;
  company_id: string | null;
  is_active: boolean;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
  company_name: string;
  phone?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

// ─── Company ───
export interface Company {
  id: string;
  name: string;
  slug: string;
  plan: string;
  settings: Record<string, unknown>;
  created_at: string;
}

// ─── Service ───
export interface Service {
  id: string;
  company_id: string;
  name: string;
  description: string | null;
  price: number;
  duration: number;
  category: string | null;
  image_url: string | null;
  is_active: boolean;
  created_at: string;
}

export interface ServiceCreate {
  name: string;
  description?: string;
  price: number;
  duration: number;
  category?: string;
  image_url?: string;
}

export interface ServiceUpdate {
  name?: string;
  description?: string;
  price?: number;
  duration?: number;
  category?: string;
  image_url?: string;
  is_active?: boolean;
}

// ─── Customer ───
export interface Customer {
  id: string;
  company_id: string;
  name: string;
  phone: string | null;
  email: string | null;
  address: string | null;
  notes: string | null;
  tags: string[];
  order_count: number;
  created_at: string;
}

export interface CustomerCreate {
  name: string;
  phone?: string;
  email?: string;
  address?: string;
  notes?: string;
  tags?: string[];
}

// ─── Staff ───
export interface Staff {
  id: string;
  company_id: string;
  name: string;
  phone: string | null;
  email: string | null;
  skills: string[];
  is_active: boolean;
  rating: number;
  current_load: number;
  order_count: number;
}

export interface StaffCreate {
  name: string;
  phone?: string;
  email?: string;
  skills?: string[];
}

// ─── Order ───
export interface OrderItem {
  service_id: string;
  service_name?: string;
  quantity: number;
  price: number;
}

export interface Order {
  id: string;
  company_id: string;
  customer_id: string;
  customer_name?: string | null;
  staff_id: string | null;
  staff_name?: string | null;
  status: OrderStatus;
  total_amount: number;
  scheduled_at: string | null;
  address: string | null;
  notes: string | null;
  items: OrderItem[];
  created_at: string;
}

export type OrderStatus =
  | 'pending'
  | 'confirmed'
  | 'dispatched'
  | 'in_progress'
  | 'completed'
  | 'cancelled';

export interface OrderCreate {
  customer_id: string;
  staff_id?: string;
  status?: string;
  total_amount: number;
  scheduled_at?: string;
  address?: string;
  notes?: string;
  items: { service_id: string; quantity: number; price: number }[];
}

// ─── AI ───
export interface ChatRequest {
  action: 'chat' | 'dispatch' | 'copywriter';
  messages: { role: 'user' | 'assistant' | 'system'; content: string }[];
  context?: Record<string, unknown>;
}

export interface ChatResponse {
  reply: string;
}

// ─── Stats ───
export interface StatsResponse {
  summary: {
    total_orders: number;
    total_customers: number;
    total_staff: number;
    total_revenue: number;
  };
  status_distribution: { status: string; count: number }[];
  last_7_days: { date: string; orders: number; revenue: number }[];
  recent_orders: Order[];
}

// ─── Common ───
export interface PaginatedResponse<T> {
  success: boolean;
  data: {
    items: T[];
    total: number;
    page: number;
    page_size: number;
  };
}
