<script>
	import { page } from '$app/state';
	import { recordId } from '#lib/navigation.js';
	import { subscriptionQuery } from './api.js';
	import SubscriptionEditor from './SubscriptionEditor.svelte';
	import { CardSkeleton, ErrorState } from '#lib/components/index.js';
	const editing = $derived(page.url.pathname.endsWith('/edit'));
	const id = $derived(editing ? recordId(page.url.pathname) : '');
	const detail = subscriptionQuery(
		() => false,
		() => id
	);
</script>

<svelte:head
	><title>{editing ? 'Edit subscription' : 'New subscription'} · Brightloop</title></svelte:head
>
{#if !editing}<SubscriptionEditor />{:else if $detail.isPending}<main id="main-content">
		<CardSkeleton />
	</main>{:else if $detail.isError}<main id="main-content">
		<ErrorState onRetry={() => $detail.refetch()} />
	</main>{:else if $detail.data}{#key id}<SubscriptionEditor
			subscription={$detail.data}
		/>{/key}{/if}
