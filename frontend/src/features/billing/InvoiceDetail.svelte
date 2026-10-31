<script>
	import { page } from '$app/state';
	import { resolve } from '$app/paths';
	import { gsap } from 'gsap';
	import { ArrowLeft, Download, Send, CreditCard, Check, X, Link as LinkIcon, Copy } from '@lucide/svelte';
	import { recordId } from '#lib/navigation.js';
	import { formatMoney, formatDate } from '#lib/format.js';
	import { notify } from '#lib/notify.js';
	import { openPdf } from '#lib/pdf.js';
	import { reveal } from '#lib/motion/reveal.js';
	import { request } from '#src/api/resources.js';
	import {
		PageHeader,
		StatusBadge,
		MoneyCell,
		CardSkeleton,
		ErrorState,
		EmptyState,
		ConfirmDialog
	} from '#lib/components/index.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import { Input } from '#lib/components/ui/input/index.js';
	import { Separator } from '#lib/components/ui/separator/index.js';
	import * as Card from '#lib/components/ui/card/index.js';
	import * as Table from '#lib/components/ui/table/index.js';
	import * as Dialog from '#lib/components/ui/dialog/index.js';
	import PaymentDialog from './PaymentDialog.svelte';
	import { useInvoice, useBillingInvalidation } from './api.js';
	/** @type {{portal?: boolean}} */
	let { portal = false } = $props();
	const id = $derived(recordId(page.url.pathname));
	const detail = useInvoice(
		() => portal,
		() => id
	);
	const invoice = $derived($detail.data);
	const actions = $derived(invoice?.allowed_actions ?? []);
	const invalidate = useBillingInvalidation();
	let paymentOpen = $state(false);
	let printing = $state(false);
	let pendingAction = $state('');
	let linkLoading = $state(false);
	let razorpayLink = $state('');
	let linkModalOpen = $state(false);

	async function createPaymentLink() {
		if (!invoice) return;
		linkLoading = true;
		try {
			const res = await request(
				'POST',
				portal ? `/me/invoices/${invoice.id}/razorpay/link` : `/invoices/${invoice.id}/razorpay/link`
			);
			razorpayLink = res.short_url || `https://rzp.io/i/${res.payment_link_id}`;
			linkModalOpen = true;
			if (typeof navigator !== 'undefined' && navigator.clipboard) {
				await navigator.clipboard.writeText(razorpayLink);
				notify.success('Razorpay payment link copied to clipboard!');
			} else {
				notify.success('Razorpay payment link generated.');
			}
		} catch (err) {
			notify.error(err);
		} finally {
			linkLoading = false;
		}
	}
	const actionLabels = {
		confirm: 'Confirm invoice',
		cancel: 'Cancel invoice',
		send: 'Send invoice'
	};
	const confirmation = $derived(
		pendingAction === 'send'
			? `Email a PDF of this invoice to ${invoice?.customer?.email ?? 'the customer’s billing email'}?`
			: pendingAction === 'cancel'
				? 'Cancel this invoice? This action changes its billing status and may not be reversible.'
				: 'Confirm this invoice and make it available for payment?'
	);
	const address = $derived(
		typeof invoice?.customer_billing?.billing_address === 'string'
			? invoice.customer_billing.billing_address
			: 'No billing address provided.'
	);
	function paidPulse(/** @type {string} */ status) {
		return (/** @type {HTMLElement} */ element) => {
			if (status !== 'paid') return;
			const media = gsap.matchMedia();
			media.add(
				'(prefers-reduced-motion: no-preference)',
				() => {
					gsap.fromTo(element, { opacity: 0.5 }, { opacity: 1, duration: 0.2, ease: 'power1.out' });
				},
				element
			);
			return () => media.revert();
		};
	}
	async function performAction() {
		if (!invoice || !actions.includes(pendingAction)) return;
		const action = pendingAction;
		await request('POST', `/invoices/${id}/${action}`);
		await invalidate();
		await $detail.refetch();
		notify.success(
			action === 'send'
				? `Invoice sent to ${invoice.customer?.email ?? 'the customer'}.`
				: action === 'cancel'
					? 'Invoice cancelled.'
					: 'Invoice confirmed.'
		);
	}
	async function print() {
		printing = true;
		try {
			await openPdf(`${portal ? '/me/invoices' : '/invoices'}/${id}/pdf`);
		} catch (error) {
			notify.error(error);
		} finally {
			printing = false;
		}
	}
	async function refresh() {
		const result = await $detail.refetch();
		return result.data;
	}
</script>

<svelte:head><title>{invoice?.number ?? 'Invoice'} · Brightloop</title></svelte:head>
<main id="main-content" class="flex flex-col gap-4">
	<div>
		<Button
			href={resolve('/[...path]', { path: `${portal ? 'portal' : 'app'}/invoices` })}
			variant="ghost"
			size="sm"
			><ArrowLeft data-icon="inline-start" />{portal ? 'My invoices' : 'All invoices'}</Button
		>
	</div>
	{#if $detail.isPending}<CardSkeleton /><CardSkeleton />{:else if $detail.isError}<ErrorState
			onRetry={() => void $detail.refetch()}
		/>{:else if !invoice}<EmptyState
			title="Invoice not found"
			description="This invoice may no longer be available."
		/>{:else}
		<div {@attach reveal}>
			<div data-reveal>
				<PageHeader
					title={invoice.number}
					subtitle={`${invoice.customer?.name ?? 'Customer'} · Issued ${formatDate(invoice.issue_date)}`}
				>
					{#snippet actions()}
						{#if !portal && invoice.allowed_actions.includes('confirm')}<Button
								variant="outline"
								onclick={() => (pendingAction = 'confirm')}
								><Check data-icon="inline-start" />Confirm</Button
							>{/if}
						{#if !portal && invoice.allowed_actions.includes('cancel')}<Button
								variant="outline"
								onclick={() => (pendingAction = 'cancel')}
								><X data-icon="inline-start" />Cancel</Button
							>{/if}
						{#if !portal && invoice.allowed_actions.includes('send')}<Button
								variant="outline"
								onclick={() => (pendingAction = 'send')}
								><Send data-icon="inline-start" />Send</Button
							>{/if}
						{#if invoice.status === 'confirmed' && Number(invoice.balance) > 0}<Button
								variant="outline"
								onclick={createPaymentLink}
								disabled={linkLoading}
								><LinkIcon data-icon="inline-start" />{linkLoading
									? 'Generating…'
									: 'Payment link'}</Button
							>{/if}
						{#if invoice.allowed_actions.includes('print')}<Button
								variant="outline"
								onclick={print}
								disabled={printing}
								><Download data-icon="inline-start" />{printing
									? 'Preparing…'
									: 'Print / Download'}</Button
							>{/if}
					{/snippet}
					{#snippet primaryAction()}{#if (portal && (invoice.allowed_actions.includes('pay') || invoice.allowed_actions.includes('record_payment'))) || (!portal && invoice.allowed_actions.includes('record_payment'))}<Button
								onclick={() => (paymentOpen = true)}
								><CreditCard data-icon="inline-start" />{portal
									? 'Pay now'
									: 'Record payment'}</Button
							>{/if}{/snippet}
				</PageHeader>
			</div>
			<div data-reveal class="mb-4 flex flex-wrap items-center gap-2">
				<span class="inline-flex" {@attach paidPulse(invoice.status)}
					><StatusBadge kind="invoice" value={invoice.status} /></span
				><StatusBadge
					kind="payment_state"
					value={invoice.payment_state}
				/>{#if invoice.is_overdue}<span class="text-xs text-destructive"
						>{invoice.days_overdue} days overdue</span
					>{/if}
			</div>
			<div class="grid gap-4 xl:grid-cols-3">
				<div data-reveal class="flex min-w-0 flex-col gap-4 xl:col-span-2">
					<Card.Root
						><Card.Header
							><Card.Title>Invoice details</Card.Title><Card.Description
								>{formatDate(invoice.period_start)} – {formatDate(
									invoice.period_end
								)}</Card.Description
							></Card.Header
						><Card.Content>
							<Table.Root
								><Table.Header
									><Table.Row
										><Table.Head>Description</Table.Head><Table.Head>Qty</Table.Head><Table.Head
											>Unit price</Table.Head
										><Table.Head>Discount</Table.Head><Table.Head>Tax</Table.Head><Table.Head
											>Total</Table.Head
										></Table.Row
									></Table.Header
								><Table.Body
									>{#each invoice.lines ?? [] as line (line.id)}<Table.Row
											><Table.Cell
												><div class="flex flex-col gap-1">
													<span class="font-medium">{line.description}</span
													>{#if line.discount?.name}<span class="text-xs text-muted-foreground"
															>{line.discount.name}</span
														>{/if}
												</div></Table.Cell
											><Table.Cell>{line.quantity}</Table.Cell><Table.Cell
												><MoneyCell value={line.unit_price} /></Table.Cell
											><Table.Cell><MoneyCell value={line.discount_amount} /></Table.Cell
											><Table.Cell
												><div class="flex flex-col gap-1 text-right">
													<span>{line.tax_rate}%</span><span class="text-xs text-muted-foreground"
														>{formatMoney(line.tax_amount)}</span
													>
												</div></Table.Cell
											><Table.Cell><MoneyCell value={line.line_total} /></Table.Cell></Table.Row
										>{/each}</Table.Body
								></Table.Root
							>
						</Card.Content></Card.Root
					>
					<Card.Root
						><Card.Header><Card.Title>Payments</Card.Title></Card.Header><Card.Content
							>{#if invoice.payments?.length}<div class="flex flex-col divide-y">
									{#each invoice.payments as payment (payment.id)}<div
											class="flex flex-wrap items-center justify-between gap-3 py-3 first:pt-0 last:pb-0"
										>
											<div class="flex flex-col gap-1">
												<span class="text-sm font-medium capitalize"
													>{payment.method?.replaceAll('_', ' ')}</span
												><span class="text-xs text-muted-foreground"
													>{formatDate(payment.paid_on)}</span
												>{#if payment.note}<p class="max-w-lg text-xs text-muted-foreground">
														{payment.note}
													</p>{/if}
											</div>
											<MoneyCell value={payment.amount} />
										</div>{/each}
								</div>{:else}<p class="text-sm text-muted-foreground">
									No payments recorded.
								</p>{/if}</Card.Content
						></Card.Root
					>
				</div>
				<aside data-reveal class="flex flex-col gap-4">
					<Card.Root
						><Card.Header
							><Card.Title>Summary</Card.Title><Card.Description
								>Due {formatDate(invoice.due_date)}</Card.Description
							></Card.Header
						><Card.Content
							><dl class="flex flex-col gap-3 text-sm">
								<div class="flex justify-between gap-4">
									<dt class="text-muted-foreground">Subtotal</dt>
									<dd>{formatMoney(invoice.subtotal)}</dd>
								</div>
								<div class="flex justify-between gap-4">
									<dt class="text-muted-foreground">Discount</dt>
									<dd>{formatMoney(invoice.discount_total)}</dd>
								</div>
								<div class="flex justify-between gap-4">
									<dt class="text-muted-foreground">Tax</dt>
									<dd>{formatMoney(invoice.tax_total)}</dd>
								</div>
								<Separator />
								<div class="flex justify-between gap-4 font-semibold">
									<dt>Invoice total</dt>
									<dd>{formatMoney(invoice.total)}</dd>
								</div>
								<div class="flex justify-between gap-4">
									<dt class="text-muted-foreground">Paid</dt>
									<dd>{formatMoney(invoice.amount_paid)}</dd>
								</div>
								<div class="flex justify-between gap-4 text-base font-semibold">
									<dt>Balance due</dt>
									<dd>{formatMoney(invoice.balance)}</dd>
								</div>
							</dl></Card.Content
						></Card.Root
					>
					<Card.Root
						><Card.Header><Card.Title>Bill to</Card.Title></Card.Header><Card.Content
							><p class="text-sm font-medium">{invoice.customer?.name}</p>
							<p class="mt-1 text-sm text-muted-foreground">{invoice.customer?.email}</p>
							<p class="mt-4 text-sm whitespace-pre-line text-muted-foreground">{address}</p>
							{#if invoice.customer_billing?.tax_id}<p class="mt-3 text-xs text-muted-foreground">
									Tax ID: {invoice.customer_billing.tax_id}
								</p>{/if}
							<div class="mt-5">
								<Button
									variant="outline"
									href={resolve('/[...path]', {
										path: `${portal ? 'portal' : 'app'}/subscriptions/${invoice.subscription?.id}`
									})}>View subscription</Button
								>
							</div></Card.Content
						></Card.Root
					>
				</aside>
			</div>
		</div>
	{/if}
</main>
<ConfirmDialog
	open={Boolean(pendingAction)}
	onOpenChange={(next) => {
		if (!next) pendingAction = '';
	}}
	title={actionLabels[/** @type {keyof typeof actionLabels} */ (pendingAction)] ?? 'Confirm action'}
	description={confirmation}
	confirmLabel={pendingAction === 'send'
		? 'Send invoice'
		: pendingAction === 'cancel'
			? 'Cancel invoice'
			: 'Confirm invoice'}
	destructive={pendingAction === 'cancel'}
	onConfirm={performAction}
/>
{#if paymentOpen && invoice}<PaymentDialog
		{invoice}
		{portal}
		open={paymentOpen}
		onOpenChange={(next) => (paymentOpen = next)}
		onSaved={refresh}
	/>{/if}
{#if linkModalOpen && invoice}
	<Dialog.Root open={linkModalOpen} onOpenChange={(next) => (linkModalOpen = next)}>
		<Dialog.Content class="sm:max-w-md">
			<Dialog.Header>
				<Dialog.Title>Razorpay Payment Link</Dialog.Title>
				<Dialog.Description>
					Share this hosted link to collect payment online for invoice {invoice.number}.
				</Dialog.Description>
			</Dialog.Header>
			<div class="flex items-center gap-2 pt-2">
				<Input readonly value={razorpayLink} class="font-mono text-xs" />
				<Button
					variant="outline"
					size="icon"
					onclick={async () => {
						if (typeof navigator !== 'undefined' && navigator.clipboard) {
							await navigator.clipboard.writeText(razorpayLink);
							notify.success('Link copied to clipboard!');
						}
					}}
				>
					<Copy class="h-4 w-4" />
				</Button>
			</div>
			<Dialog.Footer class="pt-4">
				<Button variant="outline" onclick={() => (linkModalOpen = false)}>Close</Button>
				<Button href={razorpayLink} target="_blank" rel="noopener noreferrer">
					Open link
				</Button>
			</Dialog.Footer>
		</Dialog.Content>
	</Dialog.Root>
{/if}
