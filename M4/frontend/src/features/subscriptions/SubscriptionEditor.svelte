<script>
	import { get, toStore } from 'svelte/store';
	import { untrack } from 'svelte';
	import { createQuery } from '@tanstack/svelte-query';
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { Plus, ArrowLeft, Info } from '@lucide/svelte';
	import { createActionMutation, request } from '#src/api/resources.js';
	import { createForm } from '#lib/forms/form.js';
	import { uuidSchema } from '#lib/validators.js';
	import { formatDate, formatMoney } from '#lib/format.js';
	import { notify } from '#lib/notify.js';
	import { reveal } from '#lib/motion/reveal.js';
	import { pickerQuery, customerOptions } from './api.js';
	import { initialSubscription, lineInputs, subscriptionSchema } from './forms.js';
	import SubscriptionLine from './SubscriptionLine.svelte';
	import {
		PageHeader,
		Form,
		ComboboxField,
		SelectField,
		DateField,
		MoneyCell,
		TableSkeleton,
		ErrorState,
		EmptyState
	} from '#lib/components/index.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import * as Card from '#lib/components/ui/card/index.js';
	import * as Alert from '#lib/components/ui/alert/index.js';
	import * as Field from '#lib/components/ui/field/index.js';
	/** @type {{subscription?: any}} */
	let { subscription } = $props();
	const plans = pickerQuery('/plans');
	const terms = pickerQuery('/payment-terms');
	const products = pickerQuery('/products');
	const taxes = pickerQuery('/taxes');
	const initial = untrack(() => initialSubscription(subscription));
	/** @type {ReturnType<typeof createForm> | undefined} */
	let formRef;
	const form = createForm({
		schema: subscriptionSchema(() => {
			const id = formRef ? get(formRef).values.plan_id : initial.plan_id;
			return ($plans.data?.items ?? []).find((/** @type {any} */ plan) => plan.id === id);
		}),
		initialValues: initial
	});
	formRef = form;
	const selectedPlan = $derived(
		($plans.data?.items ?? []).find((/** @type {any} */ plan) => plan.id === $form.values.plan_id)
	);
	const readOnly = $derived(Boolean(subscription && !subscription.can_edit));
	const plansOptions = $derived(
		($plans.data?.items ?? []).map((/** @type {any} */ plan) => ({
			value: plan.id,
			label: `${plan.name} · ${formatMoney(plan.price)} / ${plan.billing_period}`
		}))
	);
	const termsOptions = $derived(
		($terms.data?.items ?? []).map((/** @type {any} */ term) => ({
			value: term.id,
			label: term.name
		}))
	);
	const loading = $derived(
		$plans.isPending || $terms.isPending || $products.isPending || $taxes.isPending
	);
	const error = $derived($plans.isError || $terms.isError || $products.isError || $taxes.isError);
	$effect(() => {
		const data = $plans.data;
		if (data) untrack(() => form.validate());
	});
	const priceBody = $derived({
		plan_id: $form.values.plan_id,
		lines: lineInputs($form.values.lines)
	});
	const priceKey = $derived(JSON.stringify(priceBody));
	let settled = $state('');
	$effect(() => {
		const next = priceKey;
		const timer = setTimeout(() => (settled = next), 300);
		return () => clearTimeout(timer);
	});
	const canPreview = $derived(
		uuidSchema.safeParse(priceBody.plan_id).success &&
			priceBody.lines.every(
				(line) =>
					uuidSchema.safeParse(line.product_id).success &&
					Number.isInteger(line.quantity) &&
					line.quantity >= (selectedPlan?.min_quantity ?? 1)
			)
	);
	const preview = createQuery(
		toStore(() => ({
			queryKey: ['subscriptions', 'price-preview', settled],
			enabled: canPreview && settled === priceKey,
			retry: false,
			queryFn: (/** @type {{signal: AbortSignal}} */ { signal }) =>
				request('POST', '/subscriptions/price-preview', { body: JSON.parse(settled), signal })
		}))
	);
	const currentPreview = $derived(settled === priceKey && canPreview ? $preview.data : undefined);
	const save = createActionMutation(
		'subscriptions',
		untrack(() => (subscription ? 'PATCH' : 'POST')),
		() => (subscription ? `/subscriptions/${subscription.id}` : '/subscriptions'),
		async (data) => {
			notify.success(subscription ? 'Subscription saved.' : 'Draft created.');
			await goto(
				resolve('/[...path]', {
					path: data?.id ? `app/subscriptions/${data.id}` : 'app/subscriptions'
				})
			);
		}
	);
	function addLine() {
		form.setValue('lines', [
			...$form.values.lines,
			{
				_key: crypto.randomUUID(),
				_snapshot: [],
				product_id: '',
				quantity: selectedPlan?.min_quantity ?? 1,
				variant_value_ids: [],
				tax_id: null
			}
		]);
	}
	function removeLine(/** @type {number} */ index) {
		form.setValue(
			'lines',
			$form.values.lines.filter(
				(/** @type {any} */ _, /** @type {number} */ current) => current !== index
			)
		);
	}
	async function submit(/** @type {any} */ values) {
		const body = {
			plan_id: values.plan_id,
			payment_term_id: values.payment_term_id,
			start_date: values.start_date,
			expiry_date: values.expiry_date,
			lines: lineInputs(values.lines),
			...(!subscription ? { customer_id: values.customer_id } : {})
		};
		await $save.mutateAsync({ body });
	}
</script>

<main id="main-content" class="min-w-0" {@attach reveal}>
	<Button
		variant="ghost"
		class="mb-4"
		href={resolve('/[...path]', {
			path: subscription ? `app/subscriptions/${subscription.id}` : 'app/subscriptions'
		})}
		><ArrowLeft data-icon="inline-start" />Back to {subscription
			? 'subscription'
			: 'subscriptions'}</Button
	>
	<div data-reveal>
		<PageHeader
			title={subscription ? `Edit ${subscription.number}` : 'New subscription'}
			subtitle="Set the customer, plan, and billing dates."
		/>
	</div>
	{#if loading}<TableSkeleton />{:else if error}<ErrorState
			message="We could not load the available products and plans."
			onRetry={() => {
				void $plans.refetch();
				void $terms.refetch();
				void $products.refetch();
				void $taxes.refetch();
			}}
		/>{:else}
		{#if readOnly}<div class="mb-4">
				<Alert.Root
					><Info aria-hidden="true" /><Alert.Title>This subscription is read-only</Alert.Title
					><Alert.Description>Only editable drafts can be changed.</Alert.Description></Alert.Root
				>
			</div>{/if}
		<Form {form} onSubmit={submit}>
			<div class="grid items-start gap-4 xl:grid-cols-3">
				<div class="flex min-w-0 flex-col gap-4 xl:col-span-2">
					<Card.Root
						><Card.Header><Card.Title>Subscription details</Card.Title></Card.Header><Card.Content
							><Field.FieldGroup class="grid gap-4 md:grid-cols-2">
								<ComboboxField
									name="customer_id"
									label="Customer"
									initialLabel={subscription?.customer.name}
									loadOptions={customerOptions}
									disabled={readOnly || Boolean(subscription)}
									required
								/>
								<SelectField
									name="plan_id"
									label="Recurring plan"
									options={plansOptions}
									disabled={readOnly}
									required
								/>
								<DateField
									name="start_date"
									label="Start date"
									min={selectedPlan?.valid_from ?? undefined}
									max={selectedPlan?.valid_to ?? undefined}
									disabled={readOnly}
									required
								/>
								<DateField
									name="expiry_date"
									label="Expiry date"
									min={$form.values.start_date}
									disabled={readOnly}
									required
								/>
								<SelectField
									name="payment_term_id"
									label="Payment terms"
									options={termsOptions}
									disabled={readOnly}
									required
								/>
							</Field.FieldGroup>
							{#if selectedPlan?.valid_from || selectedPlan?.valid_to}<p
									class="mt-5 text-xs text-muted-foreground"
								>
									Plan availability: {formatDate(selectedPlan?.valid_from)} – {formatDate(
										selectedPlan?.valid_to
									)}
								</p>{/if}</Card.Content
						></Card.Root
					>
					<div class="flex items-center justify-between gap-3">
						<div>
							<h2 class="text-sm font-medium">Product lines</h2>
						</div>
						<Button
							type="button"
							variant="outline"
							disabled={readOnly || $form.isSubmitting}
							onclick={addLine}><Plus data-icon="inline-start" />Add line</Button
						>
					</div>
					{#if !$form.values.lines.length}<EmptyState
							title="No product lines"
							description="Add products or save an empty draft."
						/>{/if}
					{#each $form.values.lines as line, index (line._key)}<SubscriptionLine
							{form}
							{index}
							products={$products.data?.items ?? []}
							taxes={$taxes.data?.items ?? []}
							minimum={selectedPlan?.min_quantity ?? 1}
							preview={currentPreview?.lines?.[index]}
							disabled={readOnly}
							onRemove={() => removeLine(index)}
						/>{/each}
				</div>
				<aside class="min-w-0 xl:sticky xl:top-4">
					<Card.Root
						><Card.Header
							><Card.Title>Estimate</Card.Title><Card.Description
								>Per period, before discounts</Card.Description
							></Card.Header
						><Card.Content>
							{#if !canPreview}<p class="text-sm leading-relaxed text-muted-foreground">
									Choose a plan and products to view pricing.
								</p>{:else if settled !== priceKey || $preview.isPending || $preview.isFetching}<p
									role="status"
									class="text-sm text-muted-foreground"
								>
									Updating estimate…
								</p>{:else if $preview.isError}<ErrorState
									message="We could not refresh this estimate."
									onRetry={() => $preview.refetch()}
								/>{:else if currentPreview}
								<dl class="grid grid-cols-2 gap-4 text-sm">
									{#if currentPreview.plan_fee}<dt class="text-muted-foreground">Plan fee</dt>
										<dd><MoneyCell value={currentPreview.plan_fee.amount} /></dd>{/if}
									<dt class="text-muted-foreground">Subtotal</dt>
									<dd><MoneyCell value={currentPreview.totals?.subtotal} /></dd>
									<dt class="text-muted-foreground">Tax</dt>
									<dd><MoneyCell value={currentPreview.totals?.tax_total} /></dd>
									<dt class="border-t pt-4 font-semibold">Per period</dt>
									<dd class="border-t pt-4 font-semibold">
										<MoneyCell value={currentPreview.totals?.total} />
									</dd>
								</dl>
							{/if}
							<p class="mt-4 text-xs text-muted-foreground">Discounts apply when invoiced.</p>
						</Card.Content><Card.Footer
							><Button
								type="submit"
								class="w-full"
								disabled={readOnly || !$form.isValid || $form.isSubmitting}
								>{$form.isSubmitting
									? 'Saving…'
									: subscription
										? 'Save changes'
										: 'Create draft'}</Button
							></Card.Footer
						></Card.Root
					>
				</aside>
			</div>
		</Form>
	{/if}
</main>
