<script>
	import { page } from '$app/state';
	import { resolve } from '$app/paths';
	import { ArrowLeft, Pencil } from '@lucide/svelte';
	import { createDetailQuery } from '#src/api/resources.js';
	import { recordId } from '#lib/navigation.js';
	import { formatDate } from '#lib/format.js';
	import { reveal } from '#lib/motion/reveal.js';
	import { PageHeader, CardSkeleton, ErrorState, EmptyState } from '#lib/components/index.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import * as Card from '#lib/components/ui/card/index.js';
	import CustomerDialog from './CustomerDialog.svelte';
	import { customerName } from './schemas.js';
	const id = $derived(recordId(page.url.pathname));
	const detail = createDetailQuery(
		'customers',
		() => `/customers/${id}`,
		() => Boolean(id)
	);
	const customer = $derived($detail.data);
	let editing = $state(false);
</script>

<svelte:head
	><title>{customer ? customerName(customer) : 'Customer'} · Brightloop</title></svelte:head
>
<main id="main-content" class="flex flex-col gap-4" {@attach reveal}>
	<div>
		<Button href={resolve('/[...path]', { path: 'app/customers' })} variant="ghost" size="sm"
			><ArrowLeft data-icon="inline-start" />Customers</Button
		>
	</div>
	{#if $detail.isPending}<CardSkeleton />{:else if $detail.isError}<ErrorState
			onRetry={() => void $detail.refetch()}
		/>{:else if !customer}<EmptyState
			title="Customer not found"
			description="This customer is no longer available."
		/>{:else}<div data-reveal>
			<PageHeader
				title={customerName(customer)}
				subtitle={`Customer since ${formatDate(customer.created_at)}`}
				>{#snippet primaryAction()}<Button variant="outline" onclick={() => (editing = true)}
						><Pencil data-icon="inline-start" />Edit customer</Button
					>{/snippet}</PageHeader
			>
		</div>
		<div data-reveal class="grid gap-4 md:grid-cols-2">
			<Card.Root
				><Card.Header><Card.Title>Contact</Card.Title></Card.Header><Card.Content
					><dl class="grid grid-cols-[auto_1fr] gap-x-6 gap-y-4 text-sm">
						<dt class="text-muted-foreground">Name</dt>
						<dd>{customer.full_name || '—'}</dd>
						<dt class="text-muted-foreground">Email</dt>
						<dd class="break-all">{customer.email || '—'}</dd>
						<dt class="text-muted-foreground">Phone</dt>
						<dd>{customer.phone || '—'}</dd>
						<dt class="text-muted-foreground">Company</dt>
						<dd>{customer.company_name || '—'}</dd>
					</dl></Card.Content
				></Card.Root
			><Card.Root
				><Card.Header><Card.Title>Billing information</Card.Title></Card.Header><Card.Content
					><dl class="flex flex-col gap-4 text-sm">
						<div>
							<dt class="mb-1 text-muted-foreground">Billing address</dt>
							<dd class="whitespace-pre-line">
								{customer.billing_address || 'No address provided.'}
							</dd>
						</div>
						<div>
							<dt class="mb-1 text-muted-foreground">Tax ID</dt>
							<dd>{customer.tax_id || '—'}</dd>
						</div>
					</dl></Card.Content
				></Card.Root
			>
		</div>
		<div data-reveal class="flex flex-wrap gap-2">
			<Button
				variant="outline"
				href={`${resolve('/[...path]', { path: 'app/subscriptions' })}?customer_id=${encodeURIComponent(customer.id)}`}
				>View subscriptions</Button
			><Button
				variant="outline"
				href={`${resolve('/[...path]', { path: 'app/invoices' })}?customer_id=${encodeURIComponent(customer.id)}`}
				>View invoices</Button
			>
		</div>{/if}
</main>
{#if editing && customer}<CustomerDialog {customer} onClose={() => (editing = false)} />{/if}
