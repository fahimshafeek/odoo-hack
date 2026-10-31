<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '../lib/api';
  import { formatMoney } from '../lib/format';
  import type { Product, Plan } from '../lib/types';

  let products = $state<Product[]>([]);
  let plans = $state<Plan[]>([]);
  let selectedPlanId = $state('');

  interface LineItem {
    product_id: string;
    quantity: number;
    variant_value_ids: string[];
  }

  let lines = $state<LineItem[]>([]);
  let previewData = $state<any>(null);
  let isLoading = $state(false);

  onMount(async () => {
    try {
      const pRes = await api.getPlans('active=true&page_size=50');
      plans = pRes.items;
      if (plans.length > 0) selectedPlanId = plans[0].id;

      const prRes = await api.getProducts('active=true&page_size=50');
      const detailed = await Promise.all(
        prRes.items.map(async (p: any) => {
          try {
            return await api.getProduct(p.id);
          } catch {
            return p;
          }
        })
      );
      products = detailed;

      // Find Odoo ERP to prefill with Brand=Odoo for demo
      const odoo = products.find((p) => p.name === 'Odoo ERP');
      let odooValId = '';
      if (odoo && odoo.attributes) {
        for (const attr of odoo.attributes) {
          for (const val of attr.values) {
            if (val.name === 'Odoo') {
              odooValId = val.id;
              break;
            }
          }
        }
      }

      if (odoo) {
        lines = [
          {
            product_id: odoo.id,
            quantity: 1,
            variant_value_ids: odooValId ? [odooValId] : [],
          },
        ];
      } else if (products.length > 0) {
        lines = [{ product_id: products[0].id, quantity: 1, variant_value_ids: [] }];
      }

      updatePreview();
    } catch (err) {
      console.error(err);
    }
  });

  async function updatePreview() {
    if (lines.length === 0) {
      previewData = null;
      return;
    }
    isLoading = true;
    try {
      const res = await api.previewPricing({
        plan_id: selectedPlanId || null,
        lines,
      });
      previewData = res;
    } catch (err) {
      console.error('Pricing preview error', err);
    } finally {
      isLoading = false;
    }
  }

  function addLine() {
    if (products.length > 0) {
      lines = [...lines, { product_id: products[0].id, quantity: 1, variant_value_ids: [] }];
      updatePreview();
    }
  }

  function removeLine(idx: number) {
    lines = lines.filter((_, i) => i !== idx);
    updatePreview();
  }

  function getProductById(id: string) {
    return products.find((p) => p.id === id);
  }
</script>

<div class="space-y-6">
  <div>
    <h1 class="text-2xl font-bold text-slate-900">Live Pricing & Variant Preview</h1>
    <p class="text-sm text-slate-500 mt-1">
      Directly test the mathematical formula: <code>unit_price = product.sales_price + Σ extra_price</code> (PROD-2).
    </p>
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
    <!-- Configurator (Left) -->
    <div class="lg:col-span-7 bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-5">
      <div>
        <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">Select Subscription Plan</label>
        <select
          bind:value={selectedPlanId}
          onchange={updatePreview}
          class="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
        >
          <option value="">No Plan (Lines Only)</option>
          {#each plans as p}
            <option value={p.id}>{p.name} ({formatMoney(p.price)} / {p.billing_period})</option>
          {/each}
        </select>
      </div>

      <div>
        <div class="flex items-center justify-between mb-2">
          <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
            Configure Products & Variant Options
          </label>
          <button
            type="button"
            onclick={addLine}
            class="text-xs font-medium text-emerald-600 hover:text-emerald-700"
          >
            + Add Line
          </button>
        </div>

        <div class="space-y-3">
          {#each lines as line, i}
            {@const currentProd = getProductById(line.product_id)}
            <div class="p-3.5 bg-slate-50 rounded-xl border border-slate-200 space-y-2.5">
              <div class="flex items-center space-x-2">
                <div class="flex-1">
                  <select
                    bind:value={line.product_id}
                    onchange={() => {
                      line.variant_value_ids = [];
                      updatePreview();
                    }}
                    class="w-full px-3 py-1.5 text-xs font-medium border border-slate-300 rounded-lg bg-white"
                  >
                    {#each products as pr}
                      <option value={pr.id}>{pr.name} (Base: {formatMoney(pr.sales_price)})</option>
                    {/each}
                  </select>
                </div>
                <div class="w-24">
                  <input
                    type="number"
                    min="1"
                    bind:value={line.quantity}
                    oninput={updatePreview}
                    placeholder="Qty"
                    class="w-full px-3 py-1.5 text-xs border border-slate-300 rounded-lg bg-white text-center"
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

              {#if currentProd && currentProd.attributes && currentProd.attributes.length > 0}
                <div class="pt-1 flex flex-wrap gap-2 text-xs">
                  {#each currentProd.attributes as attr}
                    <div class="flex items-center space-x-1">
                      <span class="text-slate-500 font-medium">{attr.name}:</span>
                      <select
                        class="px-2.5 py-1 text-xs border border-slate-300 rounded-md bg-white font-medium"
                        onchange={(e) => {
                          const val = (e.target as HTMLSelectElement).value;
                          const attrValIds = attr.values.map((v) => v.id);
                          line.variant_value_ids = [
                            ...line.variant_value_ids.filter((vid) => !attrValIds.includes(vid)),
                            ...(val ? [val] : []),
                          ];
                          updatePreview();
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
    </div>

    <!-- Live Calculation Breakdown (Right) -->
    <div class="lg:col-span-5 bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
      <div class="flex items-center justify-between border-b border-slate-200 pb-3">
        <h3 class="text-sm font-bold text-slate-900 uppercase tracking-wider">Computed Calculation</h3>
        {#if isLoading}
          <span class="text-xs text-emerald-600 font-medium animate-pulse">Calculating...</span>
        {/if}
      </div>

      {#if previewData}
        <div class="space-y-3 text-xs">
          {#each previewData.lines as pl, idx}
            {@const pr = getProductById(pl.product_id)}
            <div class="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-1">
              <div class="flex justify-between font-semibold text-slate-900 text-sm">
                <span>{pr?.name || 'Line Item'} (×{lines[idx]?.quantity || 1})</span>
                <span class="tabular-nums">{formatMoney(pl.total)}</span>
              </div>
              <div class="flex justify-between text-slate-500">
                <span>Unit Price (Base + Variant Extras)</span>
                <span class="tabular-nums font-mono text-slate-800">{formatMoney(pl.unit_price)}</span>
              </div>
              <div class="flex justify-between text-slate-500">
                <span>Net Amount</span>
                <span class="tabular-nums text-slate-800">{formatMoney(pl.amount)}</span>
              </div>
              <div class="flex justify-between text-slate-500">
                <span>Tax ({pl.tax_rate}%)</span>
                <span class="tabular-nums text-slate-800">+{formatMoney(pl.tax_amount)}</span>
              </div>
            </div>
          {/each}

          {#if previewData.plan_fee}
            <div class="p-3 bg-emerald-50/50 rounded-lg border border-emerald-200 space-y-1">
              <div class="flex justify-between font-semibold text-emerald-900 text-sm">
                <span>Plan Base Fee</span>
                <span class="tabular-nums">{formatMoney(previewData.plan_fee.total)}</span>
              </div>
              <div class="flex justify-between text-emerald-700">
                <span>Fee Amount</span>
                <span class="tabular-nums">{formatMoney(previewData.plan_fee.amount)}</span>
              </div>
              <div class="flex justify-between text-emerald-700">
                <span>Tax ({previewData.plan_fee.tax_rate}%)</span>
                <span class="tabular-nums">+{formatMoney(previewData.plan_fee.tax_amount)}</span>
              </div>
            </div>
          {/if}

          <!-- Grand Summary -->
          <div class="pt-3 border-t border-slate-200 space-y-1.5">
            <div class="flex justify-between text-slate-600">
              <span>Subtotal (Pre-tax)</span>
              <span class="tabular-nums font-semibold">{formatMoney(previewData.totals.subtotal)}</span>
            </div>
            <div class="flex justify-between text-slate-600">
              <span>Total Tax (GST)</span>
              <span class="tabular-nums font-semibold">{formatMoney(previewData.totals.tax_total)}</span>
            </div>
            <div class="flex justify-between text-base font-bold text-slate-900 pt-1 border-t border-slate-100">
              <span>Total Amount</span>
              <span class="tabular-nums text-emerald-700">{formatMoney(previewData.totals.total)}</span>
            </div>
          </div>
        </div>
      {:else}
        <div class="p-8 text-center text-slate-400 text-xs">
          Add at least one line item to view live price preview.
        </div>
      {/if}
    </div>
  </div>
</div>
