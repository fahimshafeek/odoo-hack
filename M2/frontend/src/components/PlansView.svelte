<script lang="ts">
  import { onMount } from 'svelte';
  import { api, currentRole } from '../lib/api';
  import { formatMoney } from '../lib/format';
  import type { Plan } from '../lib/types';
  import PlanModal from './PlanModal.svelte';

  let plans = $state<Plan[]>([]);
  let total = $state(0);
  let isLoading = $state(true);
  let errorMessage = $state('');

  let showModal = $state(false);
  let selectedPlan = $state<Plan | null>(null);

  async function loadPlans() {
    isLoading = true;
    errorMessage = '';
    try {
      const res = await api.getPlans('page=1&page_size=50');
      plans = res.items;
      total = res.total;
    } catch (err: any) {
      errorMessage = err.message || 'Failed to load plans';
    } finally {
      isLoading = false;
    }
  }

  onMount(() => {
    loadPlans();
    const listener = () => loadPlans();
    window.addEventListener('role_changed', listener);
    return () => window.removeEventListener('role_changed', listener);
  });

  function openCreate() {
    selectedPlan = null;
    showModal = true;
  }

  function openEdit(p: Plan) {
    selectedPlan = p;
    showModal = true;
  }

  async function handleClosePlan(p: Plan) {
    if (!confirm(`Close plan '${p.name}'? It will remain active for current subscribers but cannot be sold to new ones.`)) return;
    try {
      await api.closePlan(p.id);
      loadPlans();
    } catch (err: any) {
      alert(err.message || 'Failed to close plan');
    }
  }

  async function handleDelete(p: Plan) {
    if (!confirm(`Delete or deactivate plan '${p.name}'?`)) return;
    try {
      await api.deletePlan(p.id);
      loadPlans();
    } catch (err: any) {
      alert(err.message || 'Failed to delete plan');
    }
  }
</script>

<div class="space-y-6">
  <!-- Top Bar -->
  <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
    <div>
      <h1 class="text-2xl font-bold text-slate-900">Subscription Plans</h1>
      <p class="text-sm text-slate-500 mt-1">Configure pricing terms, periods, and lifecycle rules (PLAN-1, PLAN-2).</p>
    </div>
    {#if currentRole === 'admin'}
      <button
        onclick={openCreate}
        class="inline-flex items-center px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium rounded-lg shadow-sm transition-colors"
      >
        + Add Plan
      </button>
    {/if}
  </div>

  {#if errorMessage}
    <div class="p-4 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-sm">
      {errorMessage}
    </div>
  {/if}

  <!-- Plans Table -->
  <div class="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
    <div class="overflow-x-auto">
      <table class="w-full text-left border-collapse">
        <thead>
          <tr class="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
            <th class="py-3.5 px-4">Plan Name</th>
            <th class="py-3.5 px-4">Billing Period</th>
            <th class="py-3.5 px-4">Base Fee</th>
            <th class="py-3.5 px-4">Min Qty</th>
            <th class="py-3.5 px-4">Lifecycle Rules (PLAN-2)</th>
            <th class="py-3.5 px-4">Status</th>
            {#if currentRole === 'admin'}
              <th class="py-3.5 px-4 text-right">Actions</th>
            {/if}
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100 text-sm">
          {#if isLoading}
            <tr>
              <td colspan="7" class="py-8 text-center text-slate-400">Loading plans...</td>
            </tr>
          {:else if plans.length === 0}
            <tr>
              <td colspan="7" class="py-8 text-center text-slate-400">No plans configured.</td>
            </tr>
          {:else}
            {#each plans as p}
              <tr class="hover:bg-slate-50/80 transition-colors">
                <td class="py-3.5 px-4 font-semibold text-slate-900">
                  {p.name}
                </td>
                <td class="py-3.5 px-4">
                  <span class="px-2 py-0.5 text-xs rounded font-medium capitalize bg-slate-100 text-slate-700">
                    {p.billing_period}
                  </span>
                </td>
                <td class="py-3.5 px-4 font-semibold text-slate-900 tabular-nums">
                  {formatMoney(p.price)}
                </td>
                <td class="py-3.5 px-4 text-slate-600">
                  {p.min_quantity}
                </td>
                <td class="py-3.5 px-4">
                  <div class="flex flex-wrap gap-1">
                    {#if p.allow_pause}
                      <span class="px-1.5 py-0.5 rounded text-[11px] bg-blue-50 text-blue-700 border border-blue-200">Pause</span>
                    {/if}
                    {#if p.allow_renew}
                      <span class="px-1.5 py-0.5 rounded text-[11px] bg-emerald-50 text-emerald-700 border border-emerald-200">Renew</span>
                    {/if}
                    {#if p.allow_early_close}
                      <span class="px-1.5 py-0.5 rounded text-[11px] bg-amber-50 text-amber-700 border border-amber-200">Early Close</span>
                    {/if}
                    {#if p.auto_close}
                      <span class="px-1.5 py-0.5 rounded text-[11px] bg-purple-50 text-purple-700 border border-purple-200">Auto Close</span>
                    {/if}
                  </div>
                </td>
                <td class="py-3.5 px-4">
                  {#if p.is_active}
                    <span class="px-2 py-0.5 text-xs rounded-full font-medium bg-emerald-100 text-emerald-800">Active</span>
                  {:else}
                    <span class="px-2 py-0.5 text-xs rounded-full font-medium bg-slate-100 text-slate-500">Closed</span>
                  {/if}
                </td>
                {#if currentRole === 'admin'}
                  <td class="py-3.5 px-4 text-right space-x-2">
                    <button
                      onclick={() => openEdit(p)}
                      class="text-xs text-slate-600 hover:text-slate-900 font-medium px-2 py-1 rounded hover:bg-slate-100"
                    >
                      Edit
                    </button>
                    {#if p.is_active}
                      <button
                        onclick={() => handleClosePlan(p)}
                        class="text-xs text-amber-600 hover:text-amber-800 font-medium px-2 py-1 rounded hover:bg-amber-50"
                        title="Close plan to prevent new sales"
                      >
                        Close
                      </button>
                    {/if}
                    <button
                      onclick={() => handleDelete(p)}
                      class="text-xs text-rose-600 hover:text-rose-800 font-medium px-2 py-1 rounded hover:bg-rose-50"
                    >
                      Delete
                    </button>
                  </td>
                {/if}
              </tr>
            {/each}
          {/if}
        </tbody>
      </table>
    </div>
  </div>
</div>

{#if showModal}
  <PlanModal
    plan={selectedPlan}
    onclose={() => (showModal = false)}
    onsaved={() => loadPlans()}
  />
{/if}
