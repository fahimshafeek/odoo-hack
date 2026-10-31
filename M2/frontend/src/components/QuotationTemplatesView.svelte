<script lang="ts">
  import { onMount } from 'svelte';
  import { api, currentRole } from '../lib/api';
  import { formatMoney } from '../lib/format';
  import type { QuotationTemplate } from '../lib/types';
  import TemplateModal from './TemplateModal.svelte';

  let templates = $state<QuotationTemplate[]>([]);
  let isLoading = $state(true);
  let errorMessage = $state('');

  let showModal = $state(false);
  let selectedTemplate = $state<QuotationTemplate | null>(null);

  async function loadTemplates() {
    isLoading = true;
    errorMessage = '';
    try {
      const res = await api.getTemplates('page=1&page_size=50');
      templates = res.items;
    } catch (err: any) {
      errorMessage = err.message || 'Failed to load templates';
    } finally {
      isLoading = false;
    }
  }

  onMount(() => {
    loadTemplates();
    const listener = () => loadTemplates();
    window.addEventListener('role_changed', listener);
    return () => window.removeEventListener('role_changed', listener);
  });

  function openCreate() {
    selectedTemplate = null;
    showModal = true;
  }

  async function handleOpenEdit(t: QuotationTemplate) {
    try {
      const detail = await api.getTemplate(t.id);
      selectedTemplate = detail;
      showModal = true;
    } catch (err: any) {
      alert(err.message || 'Error loading template detail');
    }
  }

  async function handleDelete(t: QuotationTemplate) {
    if (!confirm(`Delete or deactivate template '${t.name}'?`)) return;
    try {
      await api.deleteTemplate(t.id);
      loadTemplates();
    } catch (err: any) {
      alert(err.message || 'Failed to delete template');
    }
  }
</script>

<div class="space-y-6">
  <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
    <div>
      <h1 class="text-2xl font-bold text-slate-900">Quotation Templates</h1>
      <p class="text-sm text-slate-500 mt-1">Pre-configured bundles and validity terms for sales quotes (SUB-1).</p>
    </div>
    {#if currentRole === 'admin'}
      <button
        onclick={openCreate}
        class="inline-flex items-center px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium rounded-lg shadow-sm transition-colors"
      >
        + Add Quotation Template
      </button>
    {/if}
  </div>

  {#if errorMessage}
    <div class="p-4 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-sm">
      {errorMessage}
    </div>
  {/if}

  <div class="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
    <div class="overflow-x-auto">
      <table class="w-full text-left border-collapse">
        <thead>
          <tr class="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
            <th class="py-3.5 px-4">Template Name</th>
            <th class="py-3.5 px-4">Attached Plan</th>
            <th class="py-3.5 px-4">Validity</th>
            <th class="py-3.5 px-4">Line Items</th>
            <th class="py-3.5 px-4">Status</th>
            {#if currentRole === 'admin'}
              <th class="py-3.5 px-4 text-right">Actions</th>
            {/if}
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100 text-sm">
          {#if isLoading}
            <tr>
              <td colspan="6" class="py-8 text-center text-slate-400">Loading templates...</td>
            </tr>
          {:else if templates.length === 0}
            <tr>
              <td colspan="6" class="py-8 text-center text-slate-400">No quotation templates found.</td>
            </tr>
          {:else}
            {#each templates as t}
              <tr class="hover:bg-slate-50/80 transition-colors">
                <td class="py-3.5 px-4 font-semibold text-slate-900">{t.name}</td>
                <td class="py-3.5 px-4">
                  <span class="px-2 py-0.5 text-xs rounded font-medium bg-emerald-50 text-emerald-800 border border-emerald-200">
                    {t.plan.name} ({t.plan.billing_period})
                  </span>
                </td>
                <td class="py-3.5 px-4 text-slate-600">
                  {t.validity_days} days
                </td>
                <td class="py-3.5 px-4 text-slate-600">
                  {t.lines_count ?? (t.lines ? t.lines.length : 0)} items
                </td>
                <td class="py-3.5 px-4">
                  {#if t.is_active}
                    <span class="px-2 py-0.5 text-xs rounded-full font-medium bg-emerald-100 text-emerald-800">Active</span>
                  {:else}
                    <span class="px-2 py-0.5 text-xs rounded-full font-medium bg-slate-100 text-slate-500">Inactive</span>
                  {/if}
                </td>
                {#if currentRole === 'admin'}
                  <td class="py-3.5 px-4 text-right space-x-2">
                    <button
                      onclick={() => handleOpenEdit(t)}
                      class="text-xs text-slate-600 hover:text-slate-900 font-medium px-2 py-1 rounded hover:bg-slate-100"
                    >
                      Edit
                    </button>
                    <button
                      onclick={() => handleDelete(t)}
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
  <TemplateModal
    template={selectedTemplate}
    onclose={() => (showModal = false)}
    onsaved={() => loadTemplates()}
  />
{/if}
