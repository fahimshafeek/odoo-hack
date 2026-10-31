export let currentRole: 'admin' | 'staff' | 'customer' = 'admin';
let currentToken = '';

export async function setRole(role: 'admin' | 'staff' | 'customer') {
  currentRole = role;
  try {
    const res = await fetch('/auth/demo-token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role }),
    });
    if (res.ok) {
      const data = await res.json();
      currentToken = data.access_token;
    }
  } catch (err) {
    console.warn('Could not fetch demo token, using blank', err);
  }
}

// Initial token fetch
setRole('admin');

async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  if (!currentToken) {
    await setRole(currentRole);
  }

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(currentToken ? { Authorization: `Bearer ${currentToken}` } : {}),
    ...((options.headers as Record<string, string>) || {}),
  };

  const res = await fetch(path, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let errBody: any;
    try {
      errBody = await res.json();
    } catch {
      errBody = { error: { message: res.statusText, code: 'http_error' } };
    }
    const errorMsg =
      errBody?.error?.message ||
      (errBody?.error?.fields ? JSON.stringify(errBody.error.fields) : 'API Request Failed');
    throw new Error(errorMsg);
  }

  return res.json();
}

export const api = {
  // Products
  getProducts: (params = '') => apiRequest<any>(`/products?${params}`),
  getProduct: (id: string) => apiRequest<any>(`/products/${id}`),
  createProduct: (data: any) => apiRequest<any>('/products', { method: 'POST', body: JSON.stringify(data) }),
  updateProduct: (id: string, data: any) => apiRequest<any>(`/products/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteProduct: (id: string) => apiRequest<any>(`/products/${id}`, { method: 'DELETE' }),
  addAttribute: (prodId: string, data: any) =>
    apiRequest<any>(`/products/${prodId}/attributes`, { method: 'POST', body: JSON.stringify(data) }),
  updateAttribute: (prodId: string, attrId: string, data: any) =>
    apiRequest<any>(`/products/${prodId}/attributes/${attrId}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteAttribute: (prodId: string, attrId: string) =>
    apiRequest<any>(`/products/${prodId}/attributes/${attrId}`, { method: 'DELETE' }),

  // Plans
  getPlans: (params = '') => apiRequest<any>(`/plans?${params}`),
  getPlan: (id: string) => apiRequest<any>(`/plans/${id}`),
  createPlan: (data: any) => apiRequest<any>('/plans', { method: 'POST', body: JSON.stringify(data) }),
  updatePlan: (id: string, data: any) => apiRequest<any>(`/plans/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  closePlan: (id: string) => apiRequest<any>(`/plans/${id}/close`, { method: 'POST' }),
  deletePlan: (id: string) => apiRequest<any>(`/plans/${id}`, { method: 'DELETE' }),

  // Payment Terms
  getPaymentTerms: (params = '') => apiRequest<any>(`/payment-terms?${params}`),
  getPaymentTerm: (id: string) => apiRequest<any>(`/payment-terms/${id}`),
  createPaymentTerm: (data: any) => apiRequest<any>('/payment-terms', { method: 'POST', body: JSON.stringify(data) }),
  updatePaymentTerm: (id: string, data: any) => apiRequest<any>(`/payment-terms/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deletePaymentTerm: (id: string) => apiRequest<any>(`/payment-terms/${id}`, { method: 'DELETE' }),

  // Quotation Templates
  getTemplates: (params = '') => apiRequest<any>(`/quotation-templates?${params}`),
  getTemplate: (id: string) => apiRequest<any>(`/quotation-templates/${id}`),
  createTemplate: (data: any) => apiRequest<any>('/quotation-templates', { method: 'POST', body: JSON.stringify(data) }),
  updateTemplate: (id: string, data: any) => apiRequest<any>(`/quotation-templates/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteTemplate: (id: string) => apiRequest<any>(`/quotation-templates/${id}`, { method: 'DELETE' }),

  // Subscriptions (Staff / Admin)
  getSubscriptions: (params = '') => apiRequest<any>(`/subscriptions?${params}`),
  getSubscription: (id: string) => apiRequest<any>(`/subscriptions/${id}`),
  createSubscription: (data: any) => apiRequest<any>('/subscriptions', { method: 'POST', body: JSON.stringify(data) }),
  createFromTemplate: (tplId: string, data: any) => apiRequest<any>(`/subscriptions/from-template/${tplId}`, { method: 'POST', body: JSON.stringify(data) }),
  updateSubscription: (id: string, data: any) => apiRequest<any>(`/subscriptions/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteSubscription: (id: string) => apiRequest<any>(`/subscriptions/${id}`, { method: 'DELETE' }),
  transitionSubscription: (id: string, action: string, note?: string) =>
    apiRequest<any>(`/subscriptions/${id}/transition`, { method: 'POST', body: JSON.stringify({ action, note }) }),
  getSubscriptionHistory: (id: string) => apiRequest<any>(`/subscriptions/${id}/history`),

  // Price Preview
  previewPricing: (data: any) => apiRequest<any>('/subscriptions/price-preview', { method: 'POST', body: JSON.stringify(data) }),

  // Portal (Customer)
  getPortalSubscriptions: (params = '') => apiRequest<any>(`/me/subscriptions?${params}`),
  getPortalSubscription: (id: string) => apiRequest<any>(`/me/subscriptions/${id}`),
  portalAction: (id: string, action: string, note?: string) =>
    apiRequest<any>(`/me/subscriptions/${id}/actions`, { method: 'POST', body: JSON.stringify({ action, note }) }),
};
