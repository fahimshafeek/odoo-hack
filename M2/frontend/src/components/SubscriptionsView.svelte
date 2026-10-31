<script lang="ts">
  import { onMount } from 'svelte';
  import { api, currentRole } from '../lib/api';
  import { formatMoney, formatDate } from '../lib/format';
  import type { Subscription, HistoryItem, Product, Plan, QuotationTemplate } from '../lib/types';
  import StatusBadge from './StatusBadge.svelte';

  let subscriptions = $state<Subscription[]>([]);
  let total = $state(0);
  let statusFilter = $state('');
  let search = $state('');
  let isLoading = $state(true);
  let errorMessage = $state('');

  let selectedSub = $state<Subscription | null>(null);
  let historyLogs = $state<HistoryItem[]>([]);
  let isLoadingDetail = $state(false);
  let actionLoading = $state('');

  // New Subscription Drawer / Modal
  let showCreateModal = $state(false);
  let availablePlans = $state<Plan[]>([]);
  let availableProducts = $state<Product[]>([]);
  let availableTemplates = $state<QuotationTemplate[]>([]);
  let newCustomerId = $state('');
  let newPlanId = $state('');
  let newStartDate = $state(new Date().toISOString().split('T')[0]);
  let newExpiryDate = $state(
    new Date(Date.now() + 365 * 86400000).toISOString().split('T')[0]
  );
  let newLines = $state<Array<{ product_id: string; quantity: number; variant_value_ids: string[] }>>([]);

  async function loadSubscriptions() {
    isLoading = true;
    errorMessage = '';
    try {
      const q = new URLSearchParams({
        page: '1',
        page_size: '50',
        ...(statusFilter ? { status: statusFilter } : {}),
        ...(search ? { q: search } : {}),
      }).toString();

      let res;
      if (currentRole === 'customer') {
        res = await api.getPortalSubscriptions(q);
      } else {
        res = await api.getSubscriptions(q);
      }
      subscriptions = res.items;
      total = res.total;
    } catch (err: any) {
      errorMessage = err.message || 'Failed to load subscriptions';
    } finally {
      isLoading = false;
    }
  }

  async function selectSubscription(sub: Subscription) {
    isLoadingDetail = true;
    try {
      let detail: Subscription;
      let hist: HistoryItem[];

      if (currentRole === 'customer') {
        detail = await api.getPortalSubscription(sub.id);
        hist = await api.getSubscriptionHistory(sub.id);
      } else {
        detail = await api.getSubscription(sub.id);
        hist = await api.getSubscriptionHistory(sub.id);
      }

      selectedSub = detail;
      historyLogs = hist;
    } catch (err: any) {
      alert(err.message || 'Failed to load subscription details');
    } finally {
      isLoadingDetail = false;
    }
  }

  async function executeAction(action: string) {
    if (!selectedSub) return;
    actionLoading = action;
    try {
      if (currentRole === 'customer') {
        await api.portalAction(selectedSub.id, action);
      } else {
        await api.transitionSubscription(selectedSub.id, action);
      }
      // Refresh current view & list
      await selectSubscription(selectedSub);
      await loadSubscriptions();
    } catch (err: any) {
      alert(err.message || `Action '${action}' failed`);
    } finally {
      actionLoading = '';
    }
  }

  onMount(() => {
    loadSubscriptions();
    const listener = () => {
      selectedSub = null;
      loadSubscriptions();
    };
    window.addEventListener('role_changed', listener);
    return () => window.removeEventListener('role_changed', listener);
  });

  // Creation helper
  async function openCreateModal() {
    try {
      const pRes = await api.getPlans('active=true&page_size=50');
      availablePlans = pRes.items;
      if (availablePlans.length > 0) newPlanId = availablePlans[0].id;

      const prRes = await api.getProducts('active=true&page_size=50');
      availableProducts = await Promise.all(
        prRes.items.map(async (p: any) => {
          try {
            return await api.getProduct(p.id);
          } catch {
            return p;
          }
        })
      );
      if (availableProducts.length > 0) {
        newLines = [{ product_id: availableProducts[0].id, quantity: 1, variant_value_ids: [] }];
      }

      const tRes = await api.getTemplates('active=true&page_size=50');
      availableTemplates = tRes.items;

      showCreateModal = true;
    } catch (err: any) {
      alert(err.message || 'Error loading catalog for subscription creation');
    }
  }

  async function handleCreateFromTemplate(tplId: string) {
    // Pick first customer or prompt
    try {
      // Find a customer id from list
      const firstCustId = subscriptions[0]?.customer?.id;
      if (!firstCustId) {
        alert('No sample customer available in list to attach quotation');
        return;
      }
      await api.createFromTemplate(tplId, { customer_id: firstCustId });
      showCreateModal = false;
      loadSubscriptions();
    } catch (err: any) {
      alert(err.message || 'Error creating from template');
    }
  }

  async function handleCreateCustomSub(e: Event) {
    e.preventDefault();
    try {
      const firstCustId = subscriptions[0]?.customer?.id;
      if (!firstCustId) {
        alert('No sample customer available in list');
        return;
      }
      // Find payment terms
      const termRes = await api.getPaymentTerms();
      const termId = termRes.items[0]?.id;

      await api.createSubscription({
        customer_id: firstCustId,
        plan_id: newPlanId,
        start_date: newStartDate,
        expiry_date: newExpiryDate,
        payment_term_id: termId,
        lines: newLines,
      });

      showCreateModal = false;
      loadSubscriptions();
    } catch (err: any) {
      alert(err.message || 'Error creating subscription');
    }
  }
</script>

<div class="space-y-6">
  <!-- Top Bar -->
  <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
    <div>
      <h1 class="text-2xl font-bold text-slate-900">
        {currentRole === 'customer' ? 'My Subscriptions' : 'Subscriptions & Quotations'}
      </h1>
      <p class="text-sm text-slate-500 mt-1">
        {currentRole === 'customer'
          ? 'Manage your live subscriptions, pause, resume, or renew according to plan rules.'
          : 'Full lifecycle state machine (Draft → Quotation → Confirmed → Active → Paused / Closed).'}
      </p>
    </div>
    {#if currentRole !== 'customer'}
      <button
        onclick={openCreateModal}
        class="inline-flex items-center px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium rounded-lg shadow-sm transition-colors"
      >
        + New Subscription
      </button>
    {/if}
  </div>

  <!-- Filters -->
  <div class="flex flex-col sm:flex-row gap-3 bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
    <div class="flex-1">
      <input
        type="text"
        bind:value={search}
        oninput={() => loadSubscriptions()}
        placeholder="Search by SUB-number or customer name..."
        class="w-full px-3.5 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
      />
    </div>
    <div class="w-full sm:w-48">
      <select
        bind:value={statusFilter}
        onchange={() => loadSubscriptions()}
        class="w-full px-3.5 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 capitalize"
      >
        <option value="">All Statuses</option>
        {#if currentRole !== 'customer'}
          <option value="draft">Draft</option>
        {/if}
        <option value="quotation">Quotation</option>
        <option value="confirmed">Confirmed</option>
        <option value="active">Active</option>
        <option value="paused">Paused</option>
        <option value="closed">Closed</option>
      </select>
    </div>
  </div>

  {#if errorMessage}
    <div class="p-4 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-sm">
      {errorMessage}
    </div>
  {/if}

  <!-- Grid: List (Left) + Detail & Stepper (Right) -->
  <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
    <!-- Subscriptions List -->
    <div class="lg:col-span-5 bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
      <div class="px-4 py-3 bg-slate-50 border-b border-slate-200 font-semibold text-xs text-slate-500 uppercase tracking-wider">
        Subscriptions ({total})
      </div>
      <div class="divide-y divide-slate-100 max-h-[640px] overflow-y-auto">
        {#if isLoading}
          <div class="p-6 text-center text-slate-400 text-sm">Loading subscriptions...</div>
        {:else if subscriptions.length === 0}
          <div class="p-6 text-center text-slate-400 text-sm">No subscriptions found.</div>
        {:else}
          {#each subscriptions as sub}
            <button
              type="button"
              onclick={() => selectSubscription(sub)}
              class="w-full text-left p-4 hover:bg-slate-50 transition-colors flex flex-col space-y-1.5 {selectedSub?.id === sub.id ? 'bg-emerald-50/60 border-l-4 border-emerald-600' : ''}"
            >
              <div class="flex items-center justify-between">
                <span class="font-bold text-slate-900 text-sm font-mono">{sub.number}</span>
                <StatusBadge status={sub.status} />
              </div>
              <div class="flex items-center justify-between text-xs text-slate-600">
                <span class="font-medium truncate max-w-[180px]">{sub.customer.name}</span>
                <span class="font-semibold text-slate-900 tabular-nums">{formatMoney(sub.estimated_total)}</span>
              </div>
              <div class="flex items-center justify-between text-[11px] text-slate-400">
                <span>{sub.plan.name} ({sub.plan.billing_period})</span>
                <span>Exp: {formatDate(sub.expiry_date)}</span>
              </div>
            </button>
          {/each}
        {/if}
      </div>
    </div>

    <!-- Detail & Stepper Card -->
    <div class="lg:col-span-7 space-y-6">
      {#if selectedSub}
        <div class="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-6 animate-in fade-in duration-150">
          <!-- Stepper Header -->
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200 pb-4">
            <div>
              <div class="flex items-center space-x-2">
                <h2 class="text-xl font-bold font-mono text-slate-900">{selectedSub.number}</h2>
                <StatusBadge status={selectedSub.status} />
              </div>
              <p class="text-xs text-slate-500 mt-1">Customer: <strong class="text-slate-800">{selectedSub.customer.name}</strong></p>
            </div>
            <div class="text-right">
              <span class="text-xs text-slate-400 block">Estimated Total</span>
              <span class="text-xl font-bold text-slate-900 tabular-nums">{formatMoney(selectedSub.estimated_total)}</span>
            </div>
          </div>

          <!-- Visual Status Stepper (SUB-4) -->
          <div>
            <span class="text-xs font-semibold uppercase tracking-wider text-slate-500 block mb-3">Lifecycle Progress</span>
            <div class="flex items-center justify-between relative">
              <div class="absolute top-1/2 left-0 right-0 h-1 bg-slate-200 -translate-y-1/2 z-0"></div>
              {#each ['draft', 'quotation', 'confirmed', 'active'] as stepName, i}
                {@const isPast = ['draft', 'quotation', 'confirmed', 'active'].indexOf(selectedSub.status) >= i}
                {@const isCurrent = selectedSub.status === stepName}
                <div class="relative z-10 flex flex-col items-center">
                  <div
                    class="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all {isCurrent ? 'bg-emerald-600 text-white ring-4 ring-emerald-100' : isPast ? 'bg-emerald-500 text-white' : 'bg-slate-200 text-slate-600'}"
                  >
                    {i + 1}
                  </div>
                  <span class="text-[11px] font-medium mt-1 capitalize {isCurrent ? 'text-emerald-700 font-bold' : 'text-slate-500'}">
                    {stepName}
                  </span>
                </div>
              {/each}
              {#if selectedSub.status === 'paused' || selectedSub.status === 'closed'}
                <div class="relative z-10 flex flex-col items-center">
                  <div class="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold bg-amber-500 text-white ring-4 ring-amber-100">
                    !
                  </div>
                  <span class="text-[11px] font-bold mt-1 capitalize text-amber-700">
                    {selectedSub.status}
                  </span>
                </div>
              {/if}
            </div>
          </div>

          <!-- Allowed Action Triggers -->
          {#if selectedSub.allowed_actions && selectedSub.allowed_actions.length > 0}
            <div class="bg-slate-50 border border-slate-200 rounded-xl p-4">
              <span class="text-xs font-semibold text-slate-600 uppercase tracking-wider block mb-2">Available Actions</span>
              <div class="flex flex-wrap gap-2">
                {#each selectedSub.allowed_actions as act}
                  <button
                    onclick={() => executeAction(act)}
                    disabled={actionLoading === act}
                    class="px-3 py-1.5 rounded-lg text-xs font-semibold capitalize shadow-sm transition-all text-white {act === 'activate' ? 'bg-emerald-600 hover:bg-emerald-700' : act === 'confirm' ? 'bg-indigo-600 hover:bg-indigo-700' : act === 'pause' ? 'bg-amber-600 hover:bg-amber-700' : act === 'close' ? 'bg-rose-600 hover:bg-rose-700' : 'bg-slate-700 hover:bg-slate-800'}"
                  >
                    {actionLoading === act ? 'Processing...' : act.replace('_', ' ')}
                  </button>
                {/each}
              </div>
            </div>
          {/if}

          <!-- Details & Key Dates -->
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-50/70 p-3.5 rounded-lg border border-slate-200 text-xs">
            <div>
              <span class="text-slate-400 block">Plan</span>
              <span class="font-semibold text-slate-900">{selectedSub.plan.name}</span>
            </div>
            <div>
              <span class="text-slate-400 block">Start Date</span>
              <span class="font-semibold text-slate-900">{formatDate(selectedSub.start_date)}</span>
            </div>
            <div>
              <span class="text-slate-400 block">Expiry Date</span>
              <span class="font-semibold text-slate-900">{formatDate(selectedSub.expiry_date)}</span>
            </div>
            <div>
              <span class="text-slate-400 block">Next Billing</span>
              <span class="font-semibold text-emerald-700">{formatDate(selectedSub.next_billing_date)}</span>
            </div>
          </div>

          <!-- Line Items Table -->
          <div>
            <span class="text-xs font-semibold uppercase tracking-wider text-slate-500 block mb-2">Line Items Snapshot (SUB-3)</span>
            <div class="border border-slate-200 rounded-lg overflow-hidden">
              <table class="w-full text-left text-xs">
                <thead class="bg-slate-50 border-b border-slate-200 text-slate-500">
                  <tr>
                    <th class="p-2.5">Product & Variant</th>
                    <th class="p-2.5">Qty</th>
                    <th class="p-2.5">Unit Price</th>
                    <th class="p-2.5">Tax</th>
                    <th class="p-2.5 text-right">Total</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-100">
                  {#if selectedSub.lines}
                    {#each selectedSub.lines as line}
                      <tr>
                        <td class="p-2.5">
                          <span class="font-medium text-slate-900">{line.product.name}</span>
                          {#if line.variant?.selections && line.variant.selections.length > 0}
                            <div class="flex flex-wrap gap-1 mt-0.5">
                              {#each line.variant.selections as sel}
                                <span class="px-1.5 py-0.2 rounded text-[10px] bg-slate-100 text-slate-700 border border-slate-200">
                                  {sel.attribute}: <strong>{sel.value}</strong> (+{formatMoney(sel.extra_price)})
                                </span>
                              {/each}
                            </div>
                          {/if}
                        </td>
                        <td class="p-2.5 text-slate-700">{line.quantity}</td>
                        <td class="p-2.5 tabular-nums text-slate-700">{formatMoney(line.unit_price)}</td>
                        <td class="p-2.5 tabular-nums text-slate-500">{line.tax_rate}% ({formatMoney(line.tax_amount)})</td>
                        <td class="p-2.5 tabular-nums font-semibold text-slate-900 text-right">{formatMoney(line.total)}</td>
                      </tr>
                    {/each}
                  {/if}
                  {#if selectedSub.plan_fee}
                    <tr class="bg-slate-50/50">
                      <td class="p-2.5 font-medium text-slate-800" colspan="2">
                        Plan Fee ({selectedSub.plan.name})
                      </td>
                      <td class="p-2.5 tabular-nums text-slate-700">{formatMoney(selectedSub.plan_fee.amount)}</td>
                      <td class="p-2.5 tabular-nums text-slate-500">{selectedSub.plan_fee.tax_rate}% ({formatMoney(selectedSub.plan_fee.tax_amount)})</td>
                      <td class="p-2.5 tabular-nums font-semibold text-slate-900 text-right">{formatMoney(selectedSub.plan_fee.total)}</td>
                    </tr>
                  {/if}
                </tbody>
              </table>
            </div>
          </div>

          <!-- History Timeline -->
          {#if historyLogs.length > 0}
            <div>
              <span class="text-xs font-semibold uppercase tracking-wider text-slate-500 block mb-2">Audit & Transition History</span>
              <div class="border border-slate-200 rounded-lg p-3 space-y-2 bg-slate-50/50 max-h-48 overflow-y-auto text-xs">
                {#each historyLogs as log}
                  <div class="flex items-start justify-between border-b border-slate-100 pb-1.5">
                    <div>
                      <span class="font-semibold text-slate-800 capitalize">{log.action.replace('_', ' ')}:</span>
                      <span class="text-slate-500">{log.from_status} → {log.to_status}</span>
                      {#if log.note}
                        <p class="text-[11px] text-slate-600 italic mt-0.5">{log.note}</p>
                      {/if}
                    </div>
                    <span class="text-[10px] text-slate-400 whitespace-nowrap">{formatDate(log.changed_at)}</span>
                  </div>
                {/each}
              </div>
            </div>
          {/if}
        </div>
      {:else}
        <div class="bg-white border border-slate-200 rounded-xl p-12 text-center text-slate-400 shadow-sm">
          <p class="text-sm">Select a subscription from the list to view lifecycle details and execute transitions.</p>
        </div>
      {/if}
    </div>
  </div>
</div>

<!-- Modal: New Subscription / Template Picker -->
{#if showCreateModal}
  <div class="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
    <div class="bg-white rounded-xl shadow-xl max-w-xl w-full overflow-hidden border border-slate-200">
      <div class="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
        <h3 class="text-base font-semibold text-slate-900">Create Subscription</h3>
        <button onclick={() => (showCreateModal = false)} class="text-slate-400 hover:text-slate-600">✕</button>
      </div>

      <div class="p-6 space-y-6">
        <!-- Option 1: Quick from Template (D26) -->
        {#if availableTemplates.length > 0}
          <div class="border border-emerald-200 bg-emerald-50/50 p-4 rounded-xl space-y-2">
            <span class="text-xs font-bold text-emerald-800 uppercase tracking-wider block">Option 1: Quick Start From Template (D26)</span>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {#each availableTemplates as tpl}
                <button
                  type="button"
                  onclick={() => handleCreateFromTemplate(tpl.id)}
                  class="p-2.5 bg-white border border-emerald-300 rounded-lg text-left hover:bg-emerald-50 transition-colors shadow-xs"
                >
                  <span class="font-semibold text-xs text-slate-900 block">{tpl.name}</span>
                  <span class="text-[11px] text-slate-500">{tpl.plan.name} · {tpl.validity_days} days validity</span>
                </button>
              {/each}
            </div>
          </div>
        {/if}

        <!-- Option 2: Custom Subscription -->
        <form onsubmit={handleCreateCustomSub} class="space-y-4">
          <span class="text-xs font-bold text-slate-700 uppercase tracking-wider block">Option 2: Custom Draft Subscription</span>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-[11px] font-semibold text-slate-600 mb-1">
                Plan
                <select bind:value={newPlanId} class="w-full text-xs px-2.5 py-1.5 border border-slate-300 rounded-lg mt-1 font-normal">
                  {#each availablePlans as p}
                    <option value={p.id}>{p.name} ({formatMoney(p.price)})</option>
                  {/each}
                </select>
              </label>
            </div>
            <div>
              <label class="block text-[11px] font-semibold text-slate-600 mb-1">
                Start Date
                <input type="date" bind:value={newStartDate} class="w-full text-xs px-2.5 py-1.5 border border-slate-300 rounded-lg mt-1 font-normal" />
              </label>
            </div>
            <div>
              <label class="block text-[11px] font-semibold text-slate-600 mb-1">
                Expiry Date
                <input type="date" bind:value={newExpiryDate} class="w-full text-xs px-2.5 py-1.5 border border-slate-300 rounded-lg mt-1 font-normal" />
              </label>
            </div>
          </div>

          <div class="flex justify-end space-x-2 pt-2 border-t border-slate-200">
            <button
              type="button"
              onclick={() => (showCreateModal = false)}
              class="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg"
            >
              Cancel
            </button>
            <button
              type="submit"
              class="px-4 py-1.5 text-xs font-medium text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg shadow-sm"
            >
              Create Draft Subscription
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
{/if}
