<script>
	import './layout.css';
	import '@fontsource-variable/inter';
	import { QueryClient, QueryClientProvider } from '@tanstack/svelte-query';
	import { auth } from '#lib/auth/session.js';
	import favicon from '#lib/assets/favicon.svg';
	import { Toaster } from '#lib/components/ui/sonner/index.js';
	import { onMount } from 'svelte';
	/** @type {import('svelte').Component | null} */
	let PreviewToolbar = $state(null);
	onMount(() => {
		if (import.meta.env.DEV && import.meta.env.VITE_USE_MOCKS === 'true') {
			void import('#src/dev/PreviewToolbar.svelte').then(
				(module) => (PreviewToolbar = module.default)
			);
		}
	});
	const queryClient = new QueryClient({
		defaultOptions: { queries: { staleTime: 30000, retry: 1 } }
	});

	/** @type {{children: import('svelte').Snippet}} */
	let { children } = $props();
	$effect(() => {
		$auth.user?.id;
		queryClient.clear();
	});
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<a href="#main-content" class="skip-link">Skip to content</a>
<QueryClientProvider client={queryClient}>
	{#if PreviewToolbar}<PreviewToolbar />{/if}
	{@render children()}
	<Toaster position="bottom-right" />
</QueryClientProvider>
