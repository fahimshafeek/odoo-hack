<script lang="ts">
  import { onMount } from 'svelte';
  import { api, currentRole } from '../lib/api';
  import type { PaymentTerm } from '../lib/types';

  let terms = $state<PaymentTerm[]>([]);
  let isLoading = $state(true);
  let errorMessage = $state('');

  let showModal = $state(false);
  let selectedTerm = $state<PaymentTerm | null>(null);

  // Form state
  let termName = $state('');
  let dueDays = $state(30);

  async function loadTerms() {
    isLoading = true;
    errorMessage = '';
    try {
      const res = await api.getPaymentTerms();
      terms = res.items;
    } catch (err: any) {
      errorMessage = err.message || 'Failed to load payment terms';
    } finally {
      isLoading = false;
    }
  }

  onMount(() => {
    loadTerms();
    const listener = () => loadTerms();
    window.addEventListener('role_changed', listener);
    return () => window.removeEventListener('role_changed', listener);
  });

  function openCreate() {
    selectedTerm = null;
    termName = '';
    dueDays = 30;
    showModal = true;
  }

  function openEdit(term: PaymentTerm) {
    selectedTerm = term;
    termName = term.name;
    dueDays = term.due_days;
    showModal = true;
  }

  async function handleSave(e: Event) {
    e.preventDefault();
    try {
      if (selectedTerm) {
        await api.updatePaymentTerm(selectedTerm.id, { name: termName.trim(), due_days: Number(dueDays) });
      } else {
        await api.createPaymentTerm({ name: termName.trim(), due_days: Number(dueDays) });
      }
      showModal = false;
      loadTerms();
    } catch (err: any) {
      alert(err.message || 'Error saving payment term');
    }
  }

  async function handleDelete(term: PaymentTerm) {
    if (!confirm(`Delete or deactivate payment term '${term.name}'?`)) return;
    try {
      await api.deletePaymentTerm(term.id);
      loadTerms();
    } catch (err: any) {
      alert(err.message || 'Error deleting payment term');
    }
  }
</script>

<div class="space-y-6">
  <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
    <div>
      <h1 class="text-2xl font-bold text-slate-900">Payment Terms</h1>
      <p class="text-sm text-slate-500 mt-1">Configure credit periods and invoice due dates (Immediate, Net 15, Net 30, Net 60).</p>
    </div>
    {#if currentRole === 'admin'}
      <button
        onclick={openCreate}
        class="inline-flex items-center px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium rounded-lg shadow-sm transition-colors"
      >
        + Add Payment Term
      </button>
    {/if}
  </div>

  {#if errorMessage}
    <div class="p-4 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-sm">
      {errorMessage}
    </div>
  {/if}

  <div class="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm max-w-2xl">
    <table class="w-full text-left border-collapse">
      <thead>
        <tr class="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
          <th class="py-3.5 px-4">Term Name</th>
          <th class="py-3.5 px-4">Due Days</th>
          <th class="py-3.5 px-4">Status</th>
          {#if currentRole === 'admin'}
            <th class="py-3.5 px-4 text-right">Actions</th>
          {/if}
        </tr>
      </thead>
      <tbody class="divide-y divide-slate-100 text-sm">
        {#if isLoading}
          <tr>
            <td colspan="4" class="py-8 text-center text-slate-400">Loading terms...</td>
          </tr>
        {:else if terms.length === 0}
          <tr>
            <td colspan="4" class="py-8 text-center text-slate-400">No payment terms found.</td>
          </tr>
        {:else}
          {#each terms as term}
            <tr class="hover:bg-slate-50/80 transition-colors">
              <td class="py-3.5 px-4 font-semibold text-slate-900">{term.name}</td>
              <td class="py-3.5 px-4 text-slate-600">
                {term.due_days === 0 ? 'Immediate (0 days)' : `${term.due_days} days`}
              </td>
              <td class="py-3.5 px-4">
                {#if term.is_active}
                  <span class="px-2 py-0.5 text-xs rounded-full font-medium bg-emerald-100 text-emerald-800">Active</span>
                {:else}
                  <span class="px-2 py-0.5 text-xs rounded-full font-medium bg-slate-100 text-slate-500">Inactive</span>
                {/if}
              </td>
              {#if currentRole === 'admin'}
                <td class="py-3.5 px-4 text-right space-x-2">
                  <button
                    onclick={() => openEdit(term)}
                    class="text-xs text-slate-600 hover:text-slate-900 font-medium px-2 py-1 rounded hover:bg-slate-100"
                  >
                    Edit
                  </button>
                  <button
                    onclick={() => handleDelete(term)}
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

{#if showModal}
  <div class="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
    <div class="bg-white rounded-xl shadow-xl max-w-sm w-full overflow-hidden border border-slate-200">
      <div class="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
        <h3 class="text-base font-semibold text-slate-900">
          {selectedTerm ? 'Edit Payment Term' : 'New Payment Term'}
        </h3>
        <button onclick={() => (showModal = false)} class="text-slate-400 hover:text-slate-600">✕</button>
      </div>

      <form onsubmit={handleSave} class="p-6 space-y-4">
        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Term Name *
            <input
              type="text"
              required
              bind:value={termName}
              placeholder="e.g. Net 15"
              class="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 mt-1 font-normal"
            />
          </label>
        </div>

        <div>
          <label class="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Due Days (0–365) *
            <input
              type="number"
              min="0"
              max="365"
              required
              bind:value={dueDays}
              class="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 mt-1 font-normal"
            />
          </label>
        </div>

        <div class="flex justify-end space-x-2 pt-2">
          <button
            type="button"
            onclick={() => (showModal = false)}
            class="px-3.5 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 rounded-lg"
          >
            Cancel
          </button>
          <button
            type="submit"
            class="px-4 py-2 text-sm font-medium text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg"
          >
            Save Term
          </button>
        </div>
      </form>
    </div>
  </div>
{/if}
