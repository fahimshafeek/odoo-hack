<script lang="ts">
  import { onMount } from 'svelte';
  import { api, currentRole } from '../lib/api';
  import { formatMoney } from '../lib/format';
  import type { Product } from '../lib/types';
  import ProductModal from './ProductModal.svelte';

  let products = $state<Product[]>([]);
  let total = $state(0);
  let page = $state(1);
  let search = $state('');
  let typeFilter = $state('');
  let isLoading = $state(true);
  let errorMessage = $state('');

  let showModal = $state(false);
  let selectedProduct = $state<Product | null>(null);

  async function loadProducts() {
    isLoading = true;
    errorMessage = '';
    try {
      const q = new URLSearchParams({
        page: String(page),
        page_size: '20',
        ...(search ? { q: search } : {}),
        ...(typeFilter ? { type: typeFilter } : {}),
      }).toString();

      const res = await api.getProducts(q);
      // Fetch details with attributes
      const detailed = await Promise.all(
        res.items.map(async (p: any) => {
          try {
            return await api.getProduct(p.id);
          } catch {
            return p;
          }
        })
      );
      products = detailed;
      total = res.total;
    } catch (err: any) {
      errorMessage = err.message || 'Failed to load products';
    } finally {
      isLoading = false;
    }
  }

  onMount(() => {
    loadProducts();
    const listener = () => loadProducts();
    window.addEventListener('role_changed', listener);
    return () => window.removeEventListener('role_changed', listener);
  });

  function openCreate() {
    selectedProduct = null;
    showModal = true;
  }

  function openEdit(prod: Product) {
    selectedProduct = prod;
    showModal = true;
  }

  async function handleDelete(prod: Product) {
    if (!confirm(`Are you sure you want to delete or deactivate '${prod.name}'?`)) return;
    try {
      await api.deleteProduct(prod.id);
      loadProducts();
    } catch (err: any) {
      alert(err.message || 'Error deleting product');
    }
  }
</script>

<div class="space-y-6">
  <!-- Top Bar -->
  <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
    <div>
      <h1 class="text-2xl font-bold text-slate-900">Products & Variants</h1>
      <p class="text-sm text-slate-500 mt-1">Manage catalog products, variants, and extra prices (PROD-1, PROD-2).</p>
    </div>
    {#if currentRole === 'admin'}
      <button
        onclick={openCreate}
        class="inline-flex items-center px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium rounded-lg shadow-sm transition-colors"
      >
        + Add Product
      </button>
    {/if}
  </div>

  <!-- Filters -->
  <div class="flex flex-col sm:flex-row gap-3 bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
    <div class="flex-1">
      <input
        type="text"
        bind:value={search}
        oninput={() => {
          page = 1;
          loadProducts();
        }}
        placeholder="Search products by name or type..."
        class="w-full px-3.5 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
      />
    </div>
    <div class="w-full sm:w-48">
      <select
        bind:value={typeFilter}
        onchange={() => {
          page = 1;
          loadProducts();
        }}
        class="w-full px-3.5 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
      >
        <option value="">All Types</option>
        <option value="software">Software</option>
        <option value="license">License</option>
        <option value="service">Service</option>
        <option value="infrastructure">Infrastructure</option>
      </select>
    </div>
  </div>

  <!-- Error display -->
  {#if errorMessage}
    <div class="p-4 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-sm">
      {errorMessage}
    </div>
  {/if}

  <!-- Products Table -->
  <div class="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
    <div class="overflow-x-auto">
      <table class="w-full text-left border-collapse">
        <thead>
          <tr class="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
            <th class="py-3.5 px-4">Product Name</th>
            <th class="py-3.5 px-4">Type</th>
            <th class="py-3.5 px-4">Sales Price</th>
            <th class="py-3.5 px-4">Cost Price</th>
            <th class="py-3.5 px-4">Variants & Attributes</th>
            <th class="py-3.5 px-4">Status</th>
            {#if currentRole === 'admin'}
              <th class="py-3.5 px-4 text-right">Actions</th>
            {/if}
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100 text-sm">
          {#if isLoading}
            <tr>
              <td colspan="7" class="py-8 text-center text-slate-400">Loading products...</td>
            </tr>
          {:else if products.length === 0}
            <tr>
              <td colspan="7" class="py-8 text-center text-slate-400">No products found.</td>
            </tr>
          {:else}
            {#each products as prod}
              <tr class="hover:bg-slate-50/80 transition-colors">
                <td class="py-3.5 px-4">
                  <span class="font-medium text-slate-900">{prod.name}</span>
                  {#if prod.notes}
                    <p class="text-xs text-slate-500 line-clamp-1">{prod.notes}</p>
                  {/if}
                </td>
                <td class="py-3.5 px-4">
                  <span class="inline-block px-2 py-0.5 text-xs rounded bg-slate-100 text-slate-600 capitalize">
                    {prod.type}
                  </span>
                </td>
                <td class="py-3.5 px-4 font-semibold text-slate-900 tabular-nums">
                  {formatMoney(prod.sales_price)}
                </td>
                <td class="py-3.5 px-4 text-slate-600 tabular-nums">
                  {formatMoney(prod.cost_price)}
                </td>
                <td class="py-3.5 px-4">
                  {#if prod.attributes && prod.attributes.length > 0}
                    <div class="flex flex-wrap gap-1.5">
                      {#each prod.attributes as attr}
                        {#each attr.values as val}
                          <span class="inline-flex items-center px-2 py-0.5 rounded text-xs bg-slate-100 text-slate-700 border border-slate-200">
                            <span class="text-slate-400 mr-1">{attr.name}:</span>
                            <strong class="font-medium text-slate-900">{val.name}</strong>
                            {#if parseFloat(val.extra_price) > 0}
                              <span class="ml-1 text-emerald-700 font-semibold">+{formatMoney(val.extra_price)}</span>
                            {/if}
                          </span>
                        {/each}
                      {/each}
                    </div>
                  {:else}
                    <span class="text-xs text-slate-400 italic">No variants</span>
                  {/if}
                </td>
                <td class="py-3.5 px-4">
                  {#if prod.is_active}
                    <span class="px-2 py-0.5 text-xs rounded-full font-medium bg-emerald-100 text-emerald-800">Active</span>
                  {:else}
                    <span class="px-2 py-0.5 text-xs rounded-full font-medium bg-slate-100 text-slate-600">Inactive</span>
                  {/if}
                </td>
                {#if currentRole === 'admin'}
                  <td class="py-3.5 px-4 text-right space-x-2">
                    <button
                      onclick={() => openEdit(prod)}
                      class="text-xs text-slate-600 hover:text-slate-900 font-medium px-2 py-1 rounded hover:bg-slate-100"
                    >
                      Edit
                    </button>
                    <button
                      onclick={() => handleDelete(prod)}
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
  <ProductModal
    product={selectedProduct}
    onclose={() => (showModal = false)}
    onsaved={() => loadProducts()}
  />
{/if}
