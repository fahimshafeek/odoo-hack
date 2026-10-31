<script>
	import { untrack } from 'svelte';
	import { createForm } from '#lib/forms/form.js';
	import { formatMoney } from '#lib/format.js';
	import { notify } from '#lib/notify.js';
	import {
		Form,
		MoneyField,
		DateField,
		SelectField,
		TextAreaField
	} from '#lib/components/index.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import * as Dialog from '#lib/components/ui/dialog/index.js';
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
</script>

<Dialog.Root
	{open}
	onOpenChange={(/** @type {boolean} */ next) => {
		if (!$form.isSubmitting) onOpenChange(next);
	}}
	><Dialog.Content
		class="max-h-[90svh] overflow-y-auto sm:max-w-lg"
		showCloseButton={!$form.isSubmitting}
	>
		<Dialog.Header
			><Dialog.Title>{portal ? 'Pay invoice' : 'Record payment'}</Dialog.Title><Dialog.Description
				>{invoice.number} · {invoice.customer?.name ?? 'Customer'}</Dialog.Description
			></Dialog.Header
		>
		<div class="flex items-center justify-between border-b pb-4 text-sm">
			<span class="text-muted-foreground">Balance due</span><span class="font-medium tabular-nums"
				>{formatMoney(invoice.balance)}</span
			>
		</div>
		{#if portal}<p class="text-sm text-muted-foreground">
				Demo payment. No money or payment details are collected.
			</p>{/if}
		<Form {form} onSubmit={save}>
			{#if !portal}<SelectField
					name="method"
					label="Payment method"
					options={methods}
					required
				/>{/if}
			<MoneyField
				name="amount"
				label={portal ? 'Amount to pay' : 'Amount received'}
				hint={portal
					? 'Leave blank to pay the full balance.'
					: `Maximum ${formatMoney(invoice.balance)}.`}
				required={!portal}
			/>
			{#if !portal}<DateField
					name="paid_on"
					label="Payment date"
					max={today}
					required
				/><TextAreaField name="note" label="Note" hint="Optional · up to 500 characters." />{/if}
			<Dialog.Footer
				><Button variant="outline" disabled={$form.isSubmitting} onclick={() => onOpenChange(false)}
					>Cancel</Button
				><Button
					type="submit"
					disabled={!$form.isValid || $form.isSubmitting}
					aria-busy={$form.isSubmitting}
					>{$form.isSubmitting ? 'Processing…' : portal ? 'Pay now' : 'Record payment'}</Button
				></Dialog.Footer
			>
		</Form>
	</Dialog.Content></Dialog.Root
>
