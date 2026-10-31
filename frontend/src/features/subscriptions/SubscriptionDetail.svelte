<script>
	import { page } from '$app/state';
	import { resolve } from '$app/paths';
	import { ArrowLeft, ArrowUpRight, Pencil, ReceiptText } from '@lucide/svelte';
	import { createActionMutation, createDetailQuery } from '#src/api/resources.js';
	import { recordId } from '#lib/navigation.js';
	import { formatDate } from '#lib/format.js';
	import { reveal } from '#lib/motion/reveal.js';
	import { notify } from '#lib/notify.js';
	import { subscriptionQuery } from './api.js';
	import StatusStepper from './StatusStepper.svelte';
	import {
		PageHeader,
		StatusBadge,
		MoneyCell,
		ConfirmDialog,
		CardSkeleton,
		ErrorState,
		EmptyState
	} from '#lib/components/index.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import * as Card from '#lib/components/ui/card/index.js';
	import * as Table from '#lib/components/ui/table/index.js';
	/** @type {{portal?: boolean}} */
	let { portal = false } = $props();
	const id = $derived(recordId(page.url.pathname));
	const detail = subscriptionQuery(
		() => portal,
		() => id
	);
	const history = createDetailQuery(
		'subscriptions',
		() => `${portal ? '/me/subscriptions' : '/subscriptions'}/${id}/history`,
		() => Boolean(id)
	);
	const entries = $derived(
		Array.isArray($history.data) ? $history.data : ($history.data?.items ?? [])
	);
	const subscription = $derived($detail.data);
	let action = $state('');
	/** @type {Record<string, string>} */
	const labels = {
		send_quote: 'Send quote',
		confirm: 'Confirm',
		reject: 'Reject',
		activate: 'Activate',
		pause: 'Pause',
		resume: 'Resume',
		renew: 'Renew',
		close: 'Close'
	};
	const label = $derived(/** @type {Record<string,string>} */ (labels)[action] ?? 'Confirm action');
	const transition = createActionMutation(
		'subscriptions',
		'POST',
		(variables) =>
			`${portal ? '/me/subscriptions' : '/subscriptions'}/${variables.id}/${portal ? 'actions' : 'transition'}`,
		() => {
			notify.success('Subscription updated.');
		}
	);
	const confirmDescription = $derived(
		action === 'renew'
			? 'Extend this subscription by one term.'
			: action === 'close' || action === 'reject'
				? 'This will close the subscription.'
				: `Continue with “${label}” for ${subscription?.number ?? 'this subscription'}?`
	);
</script>

<svelte:head><title>{subscription?.number ?? 'Subscription'} · Brightloop</title></svelte:head>

<main id="main-content" class="min-w-0">
	<Button
		href={resolve('/[...path]', { path: `${portal ? 'portal' : 'app'}/subscriptions` })}
		variant="ghost"
		class="mb-4"
		><ArrowLeft data-icon="inline-start" />{portal ? 'My subscriptions' : 'Subscriptions'}</Button
	>
	{#if $detail.isPending}<CardSkeleton />{:else if $detail.isError}<ErrorState
			onRetry={() => $detail.refetch()}
		/>{:else if subscription}
		<div {@attach reveal}>
			<div data-reveal>
				<PageHeader
					title={subscription.number}
					subtitle={`${subscription.customer.name} · ${subscription.plan.name}`}
				>
					{#snippet actions()}<StatusBadge
							kind="subscription"
							value={subscription.status}
						/>{#if !portal && subscription.can_edit}<Button
								variant="outline"
								href={resolve('/[...path]', { path: `app/subscriptions/${id}/edit` })}
								><Pencil data-icon="inline-start" />Edit draft</Button
							>{/if}{/snippet}
					{#snippet primaryAction()}{#each subscription.allowed_actions ?? [] as allowed (allowed)}{#if /** @type {Record<string,string>} */ (labels)[allowed]}<Button
									variant={['send_quote', 'confirm', 'activate', 'resume'].includes(allowed)
										? 'default'
										: 'outline'}
									disabled={$transition.isPending}
									onclick={() => (action = allowed)}
									>{/** @type {Record<string,string>} */ (labels)[allowed]}</Button
								>{/if}{/each}{/snippet}
				</PageHeader>
			</div>
			<section data-reveal class="mb-5 border-b pb-5" aria-label="Subscription status">
				<StatusStepper
					status={subscription.status}
					history={$history.isSuccess ? entries : undefined}
				/>{#if portal && subscription.status === 'active' && !(subscription.allowed_actions ?? []).includes('pause')}<p
						class="mt-3 text-sm text-muted-foreground"
					>
						This plan does not allow pausing.
					</p>{/if}
			</section>
			<div class="grid items-start gap-4 xl:grid-cols-3">
				<div class="flex min-w-0 flex-col gap-4 xl:col-span-2">
					<Card.Root data-reveal
						><Card.Header
							><Card.Title>Items</Card.Title><Card.Description
								>Estimated per period, before discounts.</Card.Description
							></Card.Header
						><Card.Content>
							<Table.Root
								><Table.Header
									><Table.Row
										><Table.Head>Description</Table.Head><Table.Head>Qty</Table.Head><Table.Head
											>Unit price</Table.Head
										><Table.Head>Tax</Table.Head><Table.Head>Total</Table.Head></Table.Row
									></Table.Header
								><Table.Body>
									{#if subscription.plan_fee}<Table.Row
											><Table.Cell
												><p class="font-medium">{subscription.plan.name}</p>
												<p class="text-xs text-muted-foreground">Plan fee</p></Table.Cell
											><Table.Cell>1</Table.Cell><Table.Cell
												><MoneyCell value={subscription.plan_fee.amount} /></Table.Cell
											><Table.Cell>{subscription.plan_fee.tax_rate}%</Table.Cell><Table.Cell
												><MoneyCell value={subscription.plan_fee.total} /></Table.Cell
											></Table.Row
										>{/if}
									{#each subscription.lines ?? [] as line (line.id)}<Table.Row
											><Table.Cell
												><p class="font-medium">{line.product.name}</p>
												{#if line.variant?.selections?.length}<p
														class="mt-1 text-xs text-muted-foreground"
													>
														{line.variant.selections
															.map(
																(/** @type {any} */ variant) =>
																	`${variant.attribute}: ${variant.value}`
															)
															.join(' · ')}
													</p>{/if}</Table.Cell
											><Table.Cell>{line.quantity}</Table.Cell><Table.Cell
												><MoneyCell value={line.unit_price} /></Table.Cell
											><Table.Cell>{line.tax_rate}%</Table.Cell><Table.Cell
												><MoneyCell value={line.total} /></Table.Cell
											></Table.Row
										>{/each}
								</Table.Body></Table.Root
							>
							{#if !subscription.lines?.length && !subscription.plan_fee}<EmptyState
									title="No line items"
									description="Edit this draft to add products."
								/>{/if}
							<dl class="mt-6 ml-auto grid max-w-sm grid-cols-2 gap-3 border-t pt-5 text-sm">
								<dt class="text-muted-foreground">Subtotal</dt>
								<dd><MoneyCell value={subscription.totals?.subtotal} /></dd>
								<dt class="text-muted-foreground">Tax</dt>
								<dd><MoneyCell value={subscription.totals?.tax_total} /></dd>
								<dt class="font-semibold">Estimated per period</dt>
								<dd class="font-semibold"><MoneyCell value={subscription.totals?.total} /></dd>
							</dl>
						</Card.Content></Card.Root
					>
					<Card.Root data-reveal
						><Card.Header><Card.Title>History</Card.Title></Card.Header><Card.Content>
							{#if $history.isPending}<p role="status" class="text-sm text-muted-foreground">
									Loading history…
								</p>{:else if $history.isError}<ErrorState
									onRetry={() => $history.refetch()}
								/>{:else if !entries.length}<p class="text-sm text-muted-foreground">
									No history yet.
								</p>{:else}<ol class="flex flex-col gap-4 border-l pl-4">
									{#each entries as entry (entry.id)}<li>
											<div>
												<p class="text-sm font-medium capitalize">
													{String(entry.action ?? entry.to_status).replaceAll('_', ' ')}
												</p>
												<p class="mt-1 text-xs text-muted-foreground">
													{entry.changed_by?.name ?? 'System'} · {formatDate(entry.changed_at)}
												</p>
												{#if entry.note}<p class="mt-2 text-sm text-muted-foreground">
														{entry.note}
													</p>{/if}
											</div>
										</li>{/each}
								</ol>{/if}
						</Card.Content></Card.Root
					>
				</div>
				<aside class="min-w-0">
					<Card.Root data-reveal
						><Card.Header><Card.Title>Summary</Card.Title></Card.Header><Card.Content
							><dl class="grid grid-cols-2 gap-3 text-sm">
								<dt class="text-muted-foreground">Estimated / period</dt>
								<dd><MoneyCell value={subscription.estimated_total} /></dd>
								<dt class="text-muted-foreground">Billing period</dt>
								<dd class="text-right capitalize">{subscription.plan.billing_period}</dd>
								<dt class="text-muted-foreground">Starts</dt>
								<dd class="text-right">{formatDate(subscription.start_date)}</dd>
								<dt class="text-muted-foreground">Ends</dt>
								<dd class="text-right">{formatDate(subscription.expiry_date)}</dd>
								<dt class="text-muted-foreground">Next billing</dt>
								<dd class="text-right">{formatDate(subscription.next_billing_date)}</dd>
								<dt class="text-muted-foreground">Payment terms</dt>
								<dd class="text-right">{subscription.payment_term?.name}</dd>
								{#if subscription.quote_valid_until}<dt class="text-muted-foreground">
										Quote valid until
									</dt>
									<dd class="text-right">{formatDate(subscription.quote_valid_until)}</dd>{/if}
							</dl>
							<div class="mt-4 border-t pt-4">
								<p class="text-xs text-muted-foreground">Customer</p>
								<p class="mt-1 text-sm font-medium">{subscription.customer.name}</p>
								<p class="mt-1 text-xs wrap-anywhere text-muted-foreground">
									{subscription.customer.email}
								</p>
							</div>
							<p class="mt-4 text-xs text-muted-foreground">
								Discounts apply when invoiced.
							</p></Card.Content
						><Card.Footer class="flex flex-col gap-2"
							>{#if !portal}<Button
									variant="outline"
									class="w-full"
									href={resolve('/[...path]', {
										path: `app/customers/${subscription.customer.id}`
									})}>Customer details<ArrowUpRight data-icon="inline-end" /></Button
								>{/if}<Button
								variant="outline"
								class="w-full"
								href={`${resolve('/[...path]', { path: `${portal ? 'portal' : 'app'}/invoices` })}?subscription_id=${encodeURIComponent(id)}`}
								><ReceiptText data-icon="inline-start" />Related invoices</Button
							></Card.Footer
						></Card.Root
					>
				</aside>
			</div>
		</div>
	{/if}
</main>

<ConfirmDialog
	open={Boolean(action)}
	onOpenChange={(open) => {
		if (!open) action = '';
	}}
	title={label}
	description={confirmDescription}
	confirmLabel={label}
	destructive={['reject', 'close'].includes(action)}
	onConfirm={() => $transition.mutateAsync({ id, body: { action } })}
/>
