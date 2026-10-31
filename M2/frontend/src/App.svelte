<script lang="ts">
  import Navbar from './components/Navbar.svelte';
  import SubscriptionsView from './components/SubscriptionsView.svelte';
  import ProductsView from './components/ProductsView.svelte';
  import PlansView from './components/PlansView.svelte';
  import PaymentTermsView from './components/PaymentTermsView.svelte';
  import QuotationTemplatesView from './components/QuotationTemplatesView.svelte';
  import PriceCalculator from './components/PriceCalculator.svelte';

  let activeTab = $state('subscriptions');
</script>

<div class="min-h-screen flex flex-col bg-slate-50">
  <Navbar bind:activeTab />

  <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
    {#if activeTab === 'subscriptions'}
      <SubscriptionsView />
    {:else if activeTab === 'products'}
      <ProductsView />
    {:else if activeTab === 'plans'}
      <PlansView />
    {:else if activeTab === 'payment_terms'}
      <PaymentTermsView />
    {:else if activeTab === 'templates'}
      <QuotationTemplatesView />
    {:else if activeTab === 'calculator'}
      <PriceCalculator />
    {/if}
  </main>

  <footer class="bg-white border-t border-slate-200 py-6 text-center text-xs text-slate-500">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2">
      <p>Brightloop Subscription Management System · Member <strong>M2 (Catalog & Subscriptions)</strong></p>
      <p class="font-mono text-slate-400">FastAPI · SQLite · Svelte 5 · Tailwind CSS</p>
    </div>
  </footer>
</div>
