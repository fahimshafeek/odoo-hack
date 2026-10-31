<script lang="ts">
  import { setRole, currentRole } from '../lib/api';

  interface Props {
    activeTab?: string;
  }
  let { activeTab = $bindable('subscriptions') }: Props = $props();

  let role = $state<'admin' | 'staff' | 'customer'>(currentRole);

  async function handleRoleChange(newRole: 'admin' | 'staff' | 'customer') {
    role = newRole;
    await setRole(newRole);
    // Trigger custom event or global refresh if needed
    window.dispatchEvent(new CustomEvent('role_changed', { detail: newRole }));
  }
</script>

<header class="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-sm">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="flex items-center justify-between h-16">
      <!-- Logo & Domain Title -->
      <div class="flex items-center space-x-3">
        <div class="w-9 h-9 rounded-lg bg-emerald-600 flex items-center justify-center text-white font-bold text-lg shadow-sm">
          B
        </div>
        <div>
          <div class="flex items-center space-x-2">
            <span class="font-bold text-slate-900 text-lg">Brightloop</span>
            <span class="bg-emerald-50 text-emerald-700 text-xs px-2 py-0.5 rounded-md font-semibold border border-emerald-200">M2</span>
          </div>
          <p class="text-xs text-slate-500">Catalog & Subscriptions (SQLite + Svelte)</p>
        </div>
      </div>

      <!-- Navigation Tabs -->
      <nav class="hidden md:flex space-x-1">
        <button
          onclick={() => (activeTab = 'subscriptions')}
          class="px-3 py-2 rounded-md text-sm font-medium transition-colors {activeTab === 'subscriptions' ? 'bg-slate-100 text-slate-900 font-semibold' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'}"
        >
          Subscriptions
        </button>
        {#if role !== 'customer'}
          <button
            onclick={() => (activeTab = 'products')}
            class="px-3 py-2 rounded-md text-sm font-medium transition-colors {activeTab === 'products' ? 'bg-slate-100 text-slate-900 font-semibold' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'}"
          >
            Products
          </button>
          <button
            onclick={() => (activeTab = 'plans')}
            class="px-3 py-2 rounded-md text-sm font-medium transition-colors {activeTab === 'plans' ? 'bg-slate-100 text-slate-900 font-semibold' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'}"
          >
            Plans
          </button>
          <button
            onclick={() => (activeTab = 'templates')}
            class="px-3 py-2 rounded-md text-sm font-medium transition-colors {activeTab === 'templates' ? 'bg-slate-100 text-slate-900 font-semibold' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'}"
          >
            Templates
          </button>
          <button
            onclick={() => (activeTab = 'payment_terms')}
            class="px-3 py-2 rounded-md text-sm font-medium transition-colors {activeTab === 'payment_terms' ? 'bg-slate-100 text-slate-900 font-semibold' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'}"
          >
            Payment Terms
          </button>
        {/if}
        <button
          onclick={() => (activeTab = 'calculator')}
          class="px-3 py-2 rounded-md text-sm font-medium transition-colors {activeTab === 'calculator' ? 'bg-slate-100 text-slate-900 font-semibold' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'}"
        >
          Pricing Preview
        </button>
      </nav>

      <!-- Role Selector for Pairs/Demo -->
      <div class="flex items-center space-x-3">
        <span class="text-xs text-slate-500 font-medium hidden sm:inline">Role:</span>
        <div class="inline-flex rounded-lg border border-slate-200 bg-slate-50 p-1">
          <button
            type="button"
            onclick={() => handleRoleChange('admin')}
            class="px-2.5 py-1 text-xs font-medium rounded-md transition-all {role === 'admin' ? 'bg-white text-slate-900 shadow-sm font-semibold' : 'text-slate-500 hover:text-slate-900'}"
          >
            Admin
          </button>
          <button
            type="button"
            onclick={() => handleRoleChange('staff')}
            class="px-2.5 py-1 text-xs font-medium rounded-md transition-all {role === 'staff' ? 'bg-white text-slate-900 shadow-sm font-semibold' : 'text-slate-500 hover:text-slate-900'}"
          >
            Staff
          </button>
          <button
            type="button"
            onclick={() => handleRoleChange('customer')}
            class="px-2.5 py-1 text-xs font-medium rounded-md transition-all {role === 'customer' ? 'bg-white text-slate-900 shadow-sm font-semibold' : 'text-slate-500 hover:text-slate-900'}"
          >
            Customer
          </button>
        </div>
      </div>
    </div>
  </div>
</header>
