<script>
	import { untrack } from 'svelte';
	import { createForm } from '#lib/forms/form.js';
	import { formatMoney } from '#lib/format.js';
	import { notify } from '#lib/notify.js';
	import { CreditCard, Link, ExternalLink, LoaderCircle, Sparkles } from '@lucide/svelte';
	import {
		Form,
		MoneyField,
		DateField,
		SelectField,
		TextAreaField
	} from '#lib/components/index.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import * as Dialog from '#lib/components/ui/dialog/index.js';
	import * as Tabs from '#lib/components/ui/tabs/index.js';
	import { request } from '#src/api/resources.js';
	import { useBillingInvalidation } from './api.js';
	import { indiaToday, paymentSchema } from './payment-validation.js';

	/** @type {{invoice: any, portal?: boolean, open: boolean, onOpenChange: (open: boolean) => void, onSaved: () => any | Promise<any>}} */
	let { invoice, portal = false, open, onOpenChange, onSaved } = $props();
	const today = indiaToday();
	const form = untrack(() =>
		createForm({
			schema: paymentSchema(invoice.balance, today, portal),
			initialValues: portal
				? { amount: invoice.balance }
				: { method: 'bank_transfer', amount: invoice.balance, paid_on: today, note: '' }
		})
	);
	const invalidate = useBillingInvalidation();
	let razorpayLoading = $state(false);
	let activeTab = $state(untrack(() => (portal ? 'razorpay' : 'manual')));

	const methods = ['cash', 'bank_transfer', 'card', 'upi', 'cheque', 'online'].map((value) => ({
		value,
		label:
			value === 'upi'
				? 'UPI'
				: value.replaceAll('_', ' ').replace(/^./, (letter) => letter.toUpperCase())
	}));

	async function save(/** @type {any} */ values) {
		await request(
			'POST',
			portal ? `/me/invoices/${invoice.id}/pay` : `/invoices/${invoice.id}/payments`,
			{ body: values }
		);
		await invalidate();
		const updated = await onSaved();
		notify.success(updated?.status === 'paid' ? 'Invoice paid.' : 'Payment recorded.');
		onOpenChange(false);
	}

	async function payWithRazorpay() {
		razorpayLoading = true;
		try {
			const order = await request('POST', `/me/invoices/${invoice.id}/razorpay/order`);
			if (!order?.order_id) {
				throw new Error('Could not create Razorpay order');
			}
			let loaded = false;
			if (typeof window !== 'undefined') {
				if (/** @type {any} */ (window).Razorpay) {
					loaded = true;
				} else {
					loaded = await new Promise((resolve) => {
						const script = document.createElement('script');
						script.src = 'https://checkout.razorpay.com/v1/checkout.js';
						script.onload = () => resolve(true);
						script.onerror = () => resolve(false);
						document.body.appendChild(script);
					});
				}
			}

			if (loaded && /** @type {any} */ (window).Razorpay) {
				const options = {
					key: order.key_id,
					amount: order.amount,
					currency: order.currency || 'INR',
					name: 'Brightloop',
					description: `Invoice ${order.invoice_number}`,
					order_id: order.order_id,
					handler: async function (/** @type {any} */ response) {
						try {
							await request('POST', `/me/invoices/${invoice.id}/razorpay/verify`, {
								body: {
									razorpay_order_id: response.razorpay_order_id,
									razorpay_payment_id: response.razorpay_payment_id,
									razorpay_signature: response.razorpay_signature
								}
							});
							await invalidate();
							await onSaved();
							notify.success('Payment verified successfully!');
							onOpenChange(false);
						} catch (err) {
							notify.error(err);
						}
					}
				};
				const rzp = new (/** @type {any} */ (window).Razorpay)(options);
				rzp.open();
			} else {
				// Fallback to hosted payment link
				const linkRes = await request('POST', `/me/invoices/${invoice.id}/razorpay/link`);
				const url = linkRes.short_url || `https://rzp.io/i/${linkRes.payment_link_id}`;
				if (typeof window !== 'undefined') {
					window.open(url, '_blank');
				}
				notify.success('Opened Razorpay payment link.');
			}
		} catch (err) {
			notify.error(err);
		} finally {
			razorpayLoading = false;
		}
	}
</script>

<Dialog.Root
	{open}
	onOpenChange={(/** @type {boolean} */ next) => {
		if (!$form.isSubmitting && !razorpayLoading) onOpenChange(next);
	}}
>
	<Dialog.Content
		class="max-h-[90svh] overflow-y-auto sm:max-w-lg"
		showCloseButton={!$form.isSubmitting && !razorpayLoading}
	>
		<Dialog.Header>
			<Dialog.Title>{portal ? 'Pay invoice' : 'Record payment'}</Dialog.Title>
			<Dialog.Description>{invoice.number} · {invoice.customer?.name ?? 'Customer'}</Dialog.Description>
		</Dialog.Header>

		<div class="flex items-center justify-between border-b pb-4 text-sm">
			<span class="text-muted-foreground">Balance due</span>
			<span class="font-medium tabular-nums text-base">{formatMoney(invoice.balance)}</span>
		</div>

		{#if portal}
			<Tabs.Root value={activeTab} onValueChange={(val) => (activeTab = val)}>
				<Tabs.List class="grid grid-cols-2">
					<Tabs.Trigger value="razorpay">
						<CreditCard class="mr-2 h-4 w-4" />
						Razorpay
					</Tabs.Trigger>
					<Tabs.Trigger value="demo">
						<Sparkles class="mr-2 h-4 w-4" />
						Instant Demo
					</Tabs.Trigger>
				</Tabs.List>

				<Tabs.Content value="razorpay" class="flex flex-col gap-4 pt-4">
					<div class="rounded-lg border p-4 bg-muted/40 flex flex-col gap-2">
						<div class="flex items-center gap-2 font-medium text-sm">
							<CreditCard class="h-4 w-4 text-primary" />
							Online Payment via Razorpay
						</div>
						<p class="text-xs text-muted-foreground">
							Pay securely using UPI, Credit/Debit cards, Netbanking, or mobile wallets.
						</p>
					</div>

					<Dialog.Footer class="pt-2">
						<Button variant="outline" disabled={razorpayLoading} onclick={() => onOpenChange(false)}>
							Cancel
						</Button>
						<Button onclick={payWithRazorpay} disabled={razorpayLoading} aria-busy={razorpayLoading}>
							{#if razorpayLoading}
								<LoaderCircle class="mr-2 h-4 w-4 motion-safe:animate-spin" />
								Connecting…
							{:else}
								<CreditCard class="mr-2 h-4 w-4" />
								Pay {formatMoney(invoice.balance)}
							{/if}
						</Button>
					</Dialog.Footer>
				</Tabs.Content>

				<Tabs.Content value="demo" class="pt-4">
					<p class="text-xs text-muted-foreground mb-4">
						Simulate an immediate payment settlement without external gateway redirection.
					</p>
					<Form {form} onSubmit={save}>
						<MoneyField
							name="amount"
							label="Amount to pay"
							hint="Leave blank to settle full balance."
							required={false}
						/>
						<Dialog.Footer class="pt-2">
							<Button variant="outline" disabled={$form.isSubmitting} onclick={() => onOpenChange(false)}>
								Cancel
							</Button>
							<Button
								type="submit"
								disabled={!$form.isValid || $form.isSubmitting}
								aria-busy={$form.isSubmitting}
							>
								{$form.isSubmitting ? 'Processing…' : 'Settle payment'}
							</Button>
						</Dialog.Footer>
					</Form>
				</Tabs.Content>
			</Tabs.Root>
		{:else}
			<Form {form} onSubmit={save}>
				<SelectField
					name="method"
					label="Payment method"
					options={methods}
					required
				/>
				<MoneyField
					name="amount"
					label="Amount received"
					hint={`Maximum ${formatMoney(invoice.balance)}.`}
					required
				/>
				<DateField
					name="paid_on"
					label="Payment date"
					max={today}
					required
				/>
				<TextAreaField name="note" label="Note" hint="Optional · up to 500 characters." />
				<Dialog.Footer class="pt-2">
					<Button variant="outline" disabled={$form.isSubmitting} onclick={() => onOpenChange(false)}>
						Cancel
					</Button>
					<Button
						type="submit"
						disabled={!$form.isValid || $form.isSubmitting}
						aria-busy={$form.isSubmitting}
					>
						{$form.isSubmitting ? 'Processing…' : 'Record payment'}
					</Button>
				</Dialog.Footer>
			</Form>
		{/if}
	</Dialog.Content>
</Dialog.Root>
