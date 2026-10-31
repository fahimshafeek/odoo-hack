export interface TaxRef {
  id: string;
  name: string;
  rate_percent: string;
}

export interface ProductRef {
  id: string;
  name: string;
}

export interface PlanRef {
  id: string;
  name: string;
  billing_period: string;
}

export interface CustomerRef {
  id: string;
  name: string;
  email: string;
}

export interface AttributeValue {
  id: string;
  name: string;
  extra_price: string;
}

export interface ProductAttribute {
  id: string;
  name: string;
  values: AttributeValue[];
}

export interface Product {
  id: string;
  name: string;
  type: string;
  sales_price: string;
  cost_price: string;
  notes?: string | null;
  tax_id?: string | null;
  tax?: TaxRef | null;
  is_active: boolean;
  attributes?: ProductAttribute[];
  warnings?: string[];
}

export interface Plan {
  id: string;
  name: string;
  price: string;
  billing_period: 'daily' | 'weekly' | 'monthly' | 'yearly';
  min_quantity: number;
  valid_from?: string | null;
  valid_to?: string | null;
  tax?: TaxRef | null;
  tax_id?: string | null;
  auto_close: boolean;
  allow_early_close: boolean;
  allow_pause: boolean;
  allow_renew: boolean;
  is_active: boolean;
}

export interface PaymentTerm {
  id: string;
  name: string;
  due_days: number;
  is_active: boolean;
}

export interface TemplateLine {
  id: string;
  product: ProductRef;
  variant: any;
  quantity: number;
  unit_price: string;
  tax?: TaxRef | null;
  tax_rate: string;
  amount: string;
  position: number;
}

export interface QuotationTemplate {
  id: string;
  name: string;
  plan: PlanRef;
  plan_id?: string;
  validity_days: number;
  is_active: boolean;
  lines?: TemplateLine[];
  lines_count?: number;
}

export interface SubscriptionLine {
  id: string;
  product: ProductRef;
  variant: {
    selections?: Array<{
      attribute: string;
      value: string;
      extra_price: string;
    }>;
  };
  quantity: number;
  unit_price: string;
  tax?: TaxRef | null;
  tax_rate: string;
  amount: string;
  tax_amount: string;
  total: string;
}

export interface PlanFeeLine {
  amount: string;
  tax_rate: string;
  tax_amount: string;
  total: string;
}

export interface Totals {
  subtotal: string;
  tax_total: string;
  total: string;
}

export interface Subscription {
  id: string;
  number: string;
  status: 'draft' | 'quotation' | 'confirmed' | 'active' | 'paused' | 'closed';
  customer: CustomerRef;
  plan: PlanRef;
  start_date: string;
  expiry_date: string;
  next_billing_date?: string | null;
  estimated_total: string;
  allowed_actions: string[];
  payment_term?: {
    id: string;
    name: string;
    due_days: number;
  };
  quote_valid_until?: string | null;
  template_id?: string | null;
  can_edit?: boolean;
  lines?: SubscriptionLine[];
  plan_fee?: PlanFeeLine | null;
  totals?: Totals;
  created_at?: string;
}

export interface HistoryItem {
  id: string;
  from_status: string;
  to_status: string;
  action: string;
  changed_by?: { id: string; name: string } | null;
  changed_at: string;
  note?: string | null;
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
