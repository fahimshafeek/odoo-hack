<script>
	import { QueryClientProvider } from '@tanstack/svelte-query';
	import BillingRuns from '../BillingRuns.svelte';
	/** @type {{client: import('@tanstack/svelte-query').QueryClient}} */
	let { client } = $props();
</script>

<QueryClientProvider {client}><BillingRuns /></QueryClientProvider>
