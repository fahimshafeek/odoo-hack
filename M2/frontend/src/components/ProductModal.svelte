<script lang="ts">
  import { api } from '../lib/api';
  import { formatMoney } from '../lib/format';
  import type { Product } from '../lib/types';

  let { product = null, onclose = () => {}, onsaved = () => {} } = $props<{
    product?: Product | null;
    onclose?: () => void;
    onsaved?: () => void;
  }>();

  let name = $state(product ? product.name : '');
  let type = $state(product ? product.type : 'software');
  let salesPrice = $state(product ? product.sales_price : '1000.00');
  let costPrice = $state(product ? product.cost_price : '400.00');
  let notes = $state(product?.notes || '');
  let isActive = $state(product ? product.is_active : true);

  // New attribute form state
  let newAttrName = $state('');
  let newAttrValues = $state<Array<{ name: string; extra_price: string }>>([
    { name: 'Odoo', extra_price: '560.00' },
  ]);

  let errorMessage = $state('');
  let isSubmitting = $state(false);

  // Soft warning derived
  let costExceedsSales = $derived.by(() => {
    const s = parseFloat(salesPrice);
    const c = parseFloat(costPrice);
    return !isNaN(s) && !isNaN(c) && c > s;
  });

  function addValueRow() {
    newAttrValues = [...newAttrValues, { name: '', extra_price: '0.00' }];
  }

  function removeValueRow(idx: number) {
    newAttrValues = newAttrValues.filter((_, i) => i !== idx);
  }

  async function handleSubmit(e: Event) {
    e.preventDefault();
    errorMessage = '';
    isSubmitting = true;

    try {
      const payload = {
        name: name.trim(),
        type: type.trim(),
        sales_price: salesPrice,
        cost_price: costPrice,
        notes: notes ? notes.trim() : null,
        is_active: isActive,
      };

      let savedProdId: string;
      if (product) {
        const res = await api.updateProduct(product.id, payload);
        savedProdId = res.id;
      } else {
        const res = await api.createProduct(payload);
        savedProdId = res.id;

        // If user added attributes, create them
        if (newAttrName.trim() && newAttrValues.length > 0) {
          const validValues = newAttrValues
            .filter((v) => v.name.trim())
            .map((v) => ({ name: v.name.trim(), extra_price: v.extra_price || '0.00' }));
          if (validValues.length > 0) {
            await api.addAttribute(savedProdId, {
              name: newAttrName.trim(),
              values: validValues,
            });
          }
        }
      }

      onsaved();
      onclose();
    } catch (err: any) {
      errorMessage = err.message || 'Failed to save product';
    } finally {
      isSubmitting = false;
    }
  }
</script>

<div class="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
  <div class="bg-white rounded-xl shadow-xl max-w-lg w-full overflow-hidden border border-slate-200 animate-in fade-in zoom-in-95 duration-150">
    <div class="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
      <h3 class="text-base font-semibold text-slate-900">
        {product ? 'Edit Product' : 'Create New Product'}
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

      <!-- Soft warning banner -->
      {#if costExceedsSales}
        <div class="p-3 bg-amber-50 border border-amber-200 text-amber-800 text-xs rounded-lg flex items-center space-x-2">
          <span>⚠️</span>
          <span><strong>Notice:</strong> Cost price exceeds sales price. This is allowed as a soft warning.</span>
        </div>
      {/if}

      <div class="grid grid-cols-2 gap-4">
        <div class="col-span-2">
          <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">Product Name *</label>
          <input
            type="text"
            required
            bind:value={name}
            placeholder="e.g. Odoo ERP"
            class="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">Type</label>
          <select
            bind:value={type}
            class="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="software">Software</option>
            <option value="license">License</option>
            <option value="service">Service</option>
            <option value="infrastructure">Infrastructure</option>
            <option value="hardware">Hardware</option>
          </select>
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">Status</label>
          <label class="inline-flex items-center space-x-2 mt-2 cursor-pointer">
            <input type="checkbox" bind:checked={isActive} class="rounded text-emerald-600 focus:ring-emerald-500" />
            <span class="text-sm font-medium text-slate-700">Active</span>
          </label>
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">Sales Price (₹) *</label>
          <input
            type="text"
            required
            bind:value={salesPrice}
            class="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">Cost Price (₹) *</label>
          <input
            type="text"
            required
            bind:value={costPrice}
            class="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
        </div>

        <div class="col-span-2">
          <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">Notes</label>
          <textarea
            bind:value={notes}
            rows="2"
            placeholder="Product specifications or internal details..."
            class="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
          ></textarea>
        </div>
      </div>

      <!-- Add Attribute on Creation -->
      {#if !product}
        <div class="pt-3 border-t border-slate-200">
          <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
            Variant Attribute (e.g. Brand)
          </label>
          <input
            type="text"
            bind:value={newAttrName}
            placeholder="Attribute name (e.g. Brand, Tier, Edition)"
            class="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg mb-2"
          />

          {#if newAttrName}
            <div class="space-y-2 mt-2">
              <span class="text-xs text-slate-500 font-medium">Attribute Values & Extra Prices:</span>
              {#each newAttrValues as row, i}
                <div class="flex items-center space-x-2">
                  <input
                    type="text"
                    bind:value={row.name}
                    placeholder="Value (e.g. Odoo)"
                    class="flex-1 px-2.5 py-1.5 text-xs border border-slate-300 rounded-md"
                  />
                  <input
                    type="text"
                    bind:value={row.extra_price}
                    placeholder="+ Extra ₹ (e.g. 560.00)"
                    class="w-28 px-2.5 py-1.5 text-xs border border-slate-300 rounded-md"
                  />
                  {#if newAttrValues.length > 1}
                    <button type="button" onclick={() => removeValueRow(i)} class="text-rose-500 hover:text-rose-700 text-xs px-1">
                      ✕
                    </button>
                  {/if}
                </div>
              {/each}
              <button
                type="button"
                onclick={addValueRow}
                class="text-xs text-emerald-600 hover:text-emerald-700 font-medium mt-1 inline-block"
              >
                + Add another value
              </button>
            </div>
          {/if}
        </div>
      {/if}

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
          {isSubmitting ? 'Saving...' : 'Save Product'}
        </button>
      </div>
    </form>
  </div>
</div>
