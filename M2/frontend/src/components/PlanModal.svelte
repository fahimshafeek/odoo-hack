<script lang="ts">
  import { api } from '../lib/api';
  import type { Plan } from '../lib/types';

  let { plan = null, onclose = () => {}, onsaved = () => {} } = $props<{
    plan?: Plan | null;
    onclose?: () => void;
    onsaved?: () => void;
  }>();

  let name = $state(plan ? plan.name : '');
  let price = $state(plan ? plan.price : '1500.00');
  let billingPeriod = $state<'daily' | 'weekly' | 'monthly' | 'yearly'>(
    plan ? plan.billing_period : 'monthly'
  );
  let minQuantity = $state(plan ? plan.min_quantity : 1);
  let validFrom = $state(plan?.valid_from || '');
  let validTo = $state(plan?.valid_to || '');

  // 4 rule flags
  let autoClose = $state(plan ? plan.auto_close : false);
  let allowEarlyClose = $state(plan ? plan.allow_early_close : true);
  let allowPause = $state(plan ? plan.allow_pause : true);
  let allowRenew = $state(plan ? plan.allow_renew : true);
  let isActive = $state(plan ? plan.is_active : true);

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
      <button onclick={onclose} class="text-slate-400 hover:text-slate-600 rounded-md p-1">
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
          <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">Plan Name *</label>
          <input
            type="text"
            required
            bind:value={name}
            placeholder="e.g. Basic Monthly or Enterprise Yearly"
            class="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">Base Price (₹) *</label>
          <input
            type="text"
            required
            bind:value={price}
            class="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
          <span class="text-[10px] text-slate-400">Set 0 for lines-only billing</span>
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">Billing Period *</label>
          <select
            bind:value={billingPeriod}
            class="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 capitalize"
          >
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
            <option value="yearly">Yearly</option>
          </select>
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">Min Quantity</label>
          <input
            type="number"
            min="1"
            required
            bind:value={minQuantity}
            class="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">Status</label>
          <label class="inline-flex items-center space-x-2 mt-2 cursor-pointer">
            <input type="checkbox" bind:checked={isActive} class="rounded text-emerald-600 focus:ring-emerald-500" />
            <span class="text-sm font-medium text-slate-700">Active (can be sold)</span>
          </label>
        </div>
      </div>

      <!-- 4 Plan Rule Flags (PLAN-2) -->
      <div class="pt-4 border-t border-slate-200">
        <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-3">
          Lifecycle Rule Flags (PLAN-2)
        </label>
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
          onclick={onclose}
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
