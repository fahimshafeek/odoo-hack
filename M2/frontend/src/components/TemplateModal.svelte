<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '../lib/api';
  import { formatMoney } from '../lib/format';
  import type { QuotationTemplate, Plan, Product } from '../lib/types';

  let { template = null, onclose = () => {}, onsaved = () => {} } = $props<{
    template?: QuotationTemplate | null;
    onclose?: () => void;
    onsaved?: () => void;
  }>();

  let name = $state(template ? template.name : '');
  let planId = $state(template?.plan_id || (template?.plan ? template.plan.id : ''));
  let validityDays = $state(template ? template.validity_days : 30);

  let plans = $state<Plan[]>([]);
  let products = $state<Product[]>([]);

  interface FormLine {
    product_id: string;
    quantity: number;
    variant_value_ids: string[];
  }

  let lines = $state<FormLine[]>([]);
  let errorMessage = $state('');
  let isSubmitting = $state(false);

  onMount(async () => {
    try {
      const pRes = await api.getPlans('active=true&page_size=50');
      plans = pRes.items;
      if (!planId && plans.length > 0) {
        planId = plans[0].id;
      }

      const prRes = await api.getProducts('active=true&page_size=50');
      // Load details for variants
      const prodsDetailed = await Promise.all(
        prRes.items.map(async (p: any) => {
          try {
            return await api.getProduct(p.id);
          } catch {
            return p;
          }
        })
      );
      products = prodsDetailed;

      if (template && template.lines) {
        lines = template.lines.map((l: any) => ({
          product_id: l.product.id,
          quantity: l.quantity,
          variant_value_ids: l.variant?.value_ids || [],
        }));
      } else if (products.length > 0) {
        lines = [{ product_id: products[0].id, quantity: 1, variant_value_ids: [] }];
      }
    } catch (err: any) {
      errorMessage = err.message || 'Error loading dependency data';
    }
  });

  function addLine() {
    if (products.length > 0) {
      lines = [...lines, { product_id: products[0].id, quantity: 1, variant_value_ids: [] }];
    }
  }

  function removeLine(idx: number) {
    lines = lines.filter((_, i) => i !== idx);
  }

  function getProductById(id: string) {
    return products.find((p) => p.id === id);
  }

  async function handleSubmit(e: Event) {
    e.preventDefault();
    errorMessage = '';
    isSubmitting = true;

    try {
      const payload = {
        name: name.trim(),
        plan_id: planId,
        validity_days: Number(validityDays),
        lines: lines.map((l) => ({
          product_id: l.product_id,
          quantity: Number(l.quantity),
          variant_value_ids: l.variant_value_ids,
        })),
      };

      if (template) {
        await api.updateTemplate(template.id, payload);
      } else {
        await api.createTemplate(payload);
      }

      onsaved();
      onclose();
    } catch (err: any) {
      errorMessage = err.message || 'Failed to save quotation template';
    } finally {
      isSubmitting = false;
    }
  }
</script>

<div class="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
  <div class="bg-white rounded-xl shadow-xl max-w-2xl w-full overflow-hidden border border-slate-200">
    <div class="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
      <h3 class="text-base font-semibold text-slate-900">
        {template ? 'Edit Quotation Template' : 'Create Quotation Template'}
      </h3>
      <button onclick={onclose} class="text-slate-400 hover:text-slate-600">✕</button>
    </div>

    <form onsubmit={handleSubmit} class="p-6 space-y-4">
      {#if errorMessage}
        <div class="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-sm rounded-lg">
          {errorMessage}
        </div>
      {/if}

      <div class="grid grid-cols-2 gap-4">
        <div class="col-span-2">
          <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">Template Name *</label>
          <input
            type="text"
            required
            bind:value={name}
            placeholder="e.g. Standard Cloud ERP Onboarding"
            class="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">Attached Plan *</label>
          <select
            bind:value={planId}
            required
            class="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            {#each plans as p}
              <option value={p.id}>{p.name} ({formatMoney(p.price)} / {p.billing_period})</option>
            {/each}
          </select>
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">Quote Validity (Days) *</label>
          <input
            type="number"
            min="1"
            max="365"
            required
            bind:value={validityDays}
            class="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
        </div>
      </div>

      <!-- Template Line Items -->
      <div class="pt-4 border-t border-slate-200">
        <div class="flex items-center justify-between mb-2">
          <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
            Template Line Items
          </label>
          <button
            type="button"
            onclick={addLine}
            class="text-xs text-emerald-600 hover:text-emerald-700 font-medium"
          >
            + Add Line
          </button>
        </div>

        <div class="space-y-3">
          {#each lines as line, i}
            {@const currentProd = getProductById(line.product_id)}
            <div class="bg-slate-50 p-3 rounded-lg border border-slate-200 space-y-2">
              <div class="flex items-center space-x-2">
                <div class="flex-1">
                  <select
                    bind:value={line.product_id}
                    onchange={() => (line.variant_value_ids = [])}
                    class="w-full px-2.5 py-1.5 text-xs border border-slate-300 rounded-md bg-white"
                  >
                    {#each products as pr}
                      <option value={pr.id}>{pr.name} ({formatMoney(pr.sales_price)})</option>
                    {/each}
                  </select>
                </div>
                <div class="w-20">
                  <input
                    type="number"
                    min="1"
                    bind:value={line.quantity}
                    class="w-full px-2.5 py-1.5 text-xs border border-slate-300 rounded-md bg-white"
                    placeholder="Qty"
                  />
                </div>
                {#if lines.length > 1}
                  <button
                    type="button"
                    onclick={() => removeLine(i)}
                    class="text-rose-500 hover:text-rose-700 p-1 text-xs"
                  >
                    ✕
                  </button>
                {/if}
              </div>

              <!-- Variant options if product has attributes -->
              {#if currentProd && currentProd.attributes && currentProd.attributes.length > 0}
                <div class="pt-1 flex flex-wrap gap-2 text-xs">
                  {#each currentProd.attributes as attr}
                    <div class="flex items-center space-x-1">
                      <span class="text-slate-500">{attr.name}:</span>
                      <select
                        class="px-2 py-1 text-xs border border-slate-300 rounded bg-white"
                        onchange={(e) => {
                          const val = (e.target as HTMLSelectElement).value;
                          const attrValIds = attr.values.map((v) => v.id);
                          line.variant_value_ids = [
                            ...line.variant_value_ids.filter((vid) => !attrValIds.includes(vid)),
                            ...(val ? [val] : []),
                          ];
                        }}
                      >
                        <option value="">None (+₹0)</option>
                        {#each attr.values as val}
                          <option
                            value={val.id}
                            selected={line.variant_value_ids.includes(val.id)}
                          >
                            {val.name} (+{formatMoney(val.extra_price)})
                          </option>
                        {/each}
                      </select>
                    </div>
                  {/each}
                </div>
              {/if}
            </div>
          {/each}
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
          {isSubmitting ? 'Saving...' : 'Save Template'}
        </button>
      </div>
    </form>
  </div>
</div>
