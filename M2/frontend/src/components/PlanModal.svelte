<script lang="ts">
  import { api } from '../lib/api';
  import type { Plan } from '../lib/types';

  interface Props {
    plan?: Plan | null;
    onclose?: () => void;
    onsaved?: () => void;
  }

  let { plan = null, onclose = () => {}, onsaved = () => {} }: Props = $props();

  let name = $state('');
  let price = $state('1500.00');
  let billingPeriod = $state<'daily' | 'weekly' | 'monthly' | 'yearly'>('monthly');
  let minQuantity = $state(1);
  let validFrom = $state('');
  let validTo = $state('');

  // 4 rule flags
  let autoClose = $state(false);
  let allowEarlyClose = $state(true);
  let allowPause = $state(true);
  let allowRenew = $state(true);
  let isActive = $state(true);

  $effect(() => {
    if (plan) {
      name = plan.name;
      price = plan.price;
      billingPeriod = plan.billing_period;
      minQuantity = plan.min_quantity;
      validFrom = plan.valid_from || '';
      validTo = plan.valid_to || '';
      autoClose = plan.auto_close;
      allowEarlyClose = plan.allow_early_close;
      allowPause = plan.allow_pause;
      allowRenew = plan.allow_renew;
      isActive = plan.is_active;
    }
  });

  let errorMessage = $state('');
  let isSubmitting = $state(false);

  async function handleSubmit(e: Event) {
    e.preventDefault();
    errorMessage = '';
    isSubmitting = true;

    try {
      const payload = {
        name: name.trim(),
        price,
        billing_period: billingPeriod,
        min_quantity: Number(minQuantity),
        valid_from: validFrom || null,
        valid_to: validTo || null,
        auto_close: autoClose,
        allow_early_close: allowEarlyClose,
        allow_pause: allowPause,
        allow_renew: allowRenew,
        is_active: isActive,
      };

      if (plan) {
        await api.updatePlan(plan.id, payload);
      } else {
        await api.createPlan(payload);
      }

      onsaved();
      onclose();
    } catch (err: any) {
      errorMessage = err.message || 'Failed to save plan';
    } finally {
      isSubmitting = false;
    }
  }
</script>

<div class="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
  <div class="bg-white rounded-xl shadow-xl max-w-lg w-full overflow-hidden border border-slate-200">
    <div class="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
      <h3 class="text-base font-semibold text-slate-900">
        {plan ? 'Edit Subscription Plan' : 'Create New Subscription Plan'}
      </h3>
      <button onclick={() => onclose()} class="text-slate-400 hover:text-slate-600 rounded-md p-1">
        ✕
      </button>
    </div>

    <form onsubmit={handleSubmit} class="p-6 space-y-4">
      {#if errorMessage}
        <div class="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-sm rounded-lg">
          {errorMessage}
        </div>
      {/if}

      <div class="grid grid-cols-2 gap-4">
        <div class="col-span-2">
          <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Plan Name *
            <input
              type="text"
              required
              bind:value={name}
              placeholder="e.g. Basic Monthly or Enterprise Yearly"
              class="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 mt-1 font-normal"
            />
          </label>
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Base Price (₹) *
            <input
              type="text"
              required
              bind:value={price}
              class="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 mt-1 font-normal"
            />
          </label>
          <span class="text-[10px] text-slate-400">Set 0 for lines-only billing</span>
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Billing Period *
            <select
              bind:value={billingPeriod}
              class="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 capitalize mt-1 font-normal"
            >
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
              <option value="yearly">Yearly</option>
            </select>
          </label>
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Min Quantity
            <input
              type="number"
              min="1"
              required
              bind:value={minQuantity}
              class="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 mt-1 font-normal"
            />
          </label>
        </div>

        <div>
          <span class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">Status</span>
          <label class="inline-flex items-center space-x-2 mt-2 cursor-pointer">
            <input type="checkbox" bind:checked={isActive} class="rounded text-emerald-600 focus:ring-emerald-500" />
            <span class="text-sm font-medium text-slate-700">Active (can be sold)</span>
          </label>
        </div>
      </div>

      <!-- 4 Plan Rule Flags (PLAN-2) -->
      <div class="pt-4 border-t border-slate-200">
        <span class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-3">
          Lifecycle Rule Flags (PLAN-2)
        </span>
        <div class="space-y-3 bg-slate-50 p-3.5 rounded-lg border border-slate-200">
          <label class="flex items-start space-x-3 cursor-pointer">
            <input type="checkbox" bind:checked={allowPause} class="rounded text-emerald-600 mt-0.5 focus:ring-emerald-500" />
            <div>
              <span class="text-xs font-semibold text-slate-800">Allow Pause</span>
              <p class="text-[11px] text-slate-500">Subscribers can pause subscriptions without being billed.</p>
            </div>
          </label>

          <label class="flex items-start space-x-3 cursor-pointer">
            <input type="checkbox" bind:checked={allowRenew} class="rounded text-emerald-600 mt-0.5 focus:ring-emerald-500" />
            <div>
              <span class="text-xs font-semibold text-slate-800">Allow Renew</span>
              <p class="text-[11px] text-slate-500">Subscribers and staff can renew subscriptions and extend expiry.</p>
            </div>
          </label>

          <label class="flex items-start space-x-3 cursor-pointer">
            <input type="checkbox" bind:checked={allowEarlyClose} class="rounded text-emerald-600 mt-0.5 focus:ring-emerald-500" />
            <div>
              <span class="text-xs font-semibold text-slate-800">Allow Early Close</span>
              <p class="text-[11px] text-slate-500">Permit closing the subscription before the expiry date.</p>
            </div>
          </label>

          <label class="flex items-start space-x-3 cursor-pointer">
            <input type="checkbox" bind:checked={autoClose} class="rounded text-emerald-600 mt-0.5 focus:ring-emerald-500" />
            <div>
              <span class="text-xs font-semibold text-slate-800">Auto-close at End</span>
              <p class="text-[11px] text-slate-500">Nightly worker automatically closes expired subscriptions.</p>
            </div>
          </label>
        </div>
      </div>

      <div class="flex justify-end space-x-3 pt-4 border-t border-slate-200">
        <button
          type="button"
          onclick={() => onclose()}
          class="px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={isSubmitting}
          class="px-4 py-2 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 disabled:opacity-50"
        >
          {isSubmitting ? 'Saving...' : 'Save Plan'}
        </button>
      </div>
    </form>
  </div>
</div>
