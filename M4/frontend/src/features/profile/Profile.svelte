<script>
	import { createDetailQuery } from '#src/api/resources.js';
	import { reveal } from '#lib/motion/reveal.js';
	import { PageHeader, CardSkeleton, ErrorState, EmptyState } from '#lib/components/index.js';
	import * as Card from '#lib/components/ui/card/index.js';
	import ProfileForm from './ProfileForm.svelte';
	const profile = createDetailQuery('profile', '/me/profile');
</script>

<svelte:head><title>Profile · Brightloop</title></svelte:head>
<main id="main-content" class="flex flex-col gap-4" {@attach reveal}>
	<div data-reveal>
		<PageHeader title="Profile" subtitle="Your contact and billing information." />
	</div>
	<div data-reveal class="max-w-2xl">
		{#if $profile.isPending}<CardSkeleton />{:else if $profile.isError}<ErrorState
				onRetry={() => void $profile.refetch()}
			/>{:else if !$profile.data}<EmptyState
				title="Profile unavailable"
				description="Your account does not have a linked customer profile."
			/>{:else}<Card.Root
				><Card.Header
					><Card.Title>Account details</Card.Title><Card.Description
						>Used for subscription billing and invoices.</Card.Description
					></Card.Header
				><Card.Content><ProfileForm profile={$profile.data} /></Card.Content></Card.Root
			>{/if}
	</div>
</main>
