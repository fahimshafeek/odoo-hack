<script>
	import { z } from 'zod';
	import { Repeat2 } from '@lucide/svelte';
	import { reveal } from '#lib/motion/reveal.js';
	import { statuses } from '#lib/status.js';
	import { createForm } from '#lib/forms/form.js';
	import {
		dateSchema,
		moneySchema,
		notesSchema,
		personNameSchema,
		quantitySchema
	} from '#lib/validators.js';
	import { notify } from '#lib/notify.js';
	import PageHeader from '#lib/components/PageHeader.svelte';
	import DataTable from '#lib/components/DataTable.svelte';
	import StatusBadge from '#lib/components/StatusBadge.svelte';
	import MoneyCell from '#lib/components/MoneyCell.svelte';
	import Form from '#lib/components/Form.svelte';
	import TextField from '#lib/components/TextField.svelte';
	import NumberField from '#lib/components/NumberField.svelte';
	import MoneyField from '#lib/components/MoneyField.svelte';
	import DateField from '#lib/components/DateField.svelte';
	import SelectField from '#lib/components/SelectField.svelte';
	import SwitchField from '#lib/components/SwitchField.svelte';
	import TextAreaField from '#lib/components/TextAreaField.svelte';
	import ConfirmDialog from '#lib/components/ConfirmDialog.svelte';
	import FilterBar from '#lib/components/FilterBar.svelte';
	import SearchInput from '#lib/components/SearchInput.svelte';
	import { Button } from '#lib/components/ui/button/index.js';
	import { Switch } from '#lib/components/ui/switch/index.js';
	import * as Card from '#lib/components/ui/card/index.js';

	const form = createForm({
		schema: z.object({
			name: personNameSchema,
			quantity: quantitySchema(5),
			amount: moneySchema,
			date: dateSchema,
			interval: z.enum(['monthly', 'yearly']),
			active: z.boolean(),
			notes: notesSchema()
		}),
		initialValues: {
			name: '',
			quantity: 5,
			amount: '',
			date: '',
			interval: 'monthly',
			active: true,
			notes: ''
		}
	});
	let confirmOpen = $state(false);
	let loading = $state(false);
	let failed = $state(false);
	let params = $state({ page: 1, page_size: 25, sort: 'state', q: '' });
	const data = $derived({
		items: Object.keys(statuses.subscription)
			.filter((state) => state.includes(params.q.toLowerCase()))
			.map((state) => ({ id: state, state })),
		total: Object.keys(statuses.subscription).filter((state) =>
			state.includes(params.q.toLowerCase())
		).length,
		page: 1,
		page_size: 25
	});
	const columns = $derived([
		{ key: 'state', header: 'Status', cell: statusCell },
		{ key: 'id', header: 'API value' }
	]);
</script>

<svelte:head
	><title>Design system · Brightloop</title><meta name="robots" content="noindex" /></svelte:head
>

{#snippet statusCell(row = { state: 'draft' })}<StatusBadge
		kind="subscription"
		value={row.state}
	/>{/snippet}
<main id="main-content" class="mx-auto max-w-6xl px-4 py-12 md:px-6" {@attach reveal}>
	<div data-reveal>
		<PageHeader
			title="A shared visual language"
			subtitle="Brightloop’s components, forms, and interaction states. This workshop is available during development."
		>
			{#snippet primaryAction()}<Button onclick={() => (confirmOpen = true)}
					>Try confirmation</Button
				>{/snippet}
		</PageHeader>
	</div>
	<div class="grid gap-8 lg:grid-cols-2">
		<Card.Root data-reveal
			><Card.Header
				><Card.Title>Form foundations</Card.Title><Card.Description
					>Try invalid inputs, keyboard navigation, and inline feedback.</Card.Description
				></Card.Header
			><Card.Content>
				<Form
					{form}
					onSubmit={() => notify.success('The form is valid. This workshop does not save records.')}
				>
					<TextField name="name" label="Workspace label" required /><NumberField
						name="quantity"
						label="Quantity"
						hint="Minimum 5."
						min={5}
						required
					/><MoneyField name="amount" label="Amount" required /><DateField
						name="date"
						label="Date"
						required
					/>
					<SelectField
						name="interval"
						label="Billing interval"
						options={[
							{ value: 'monthly', label: 'Monthly' },
							{ value: 'yearly', label: 'Yearly' }
						]}
					/><SwitchField name="active" label="Active" /><TextAreaField name="notes" label="Notes" />
					<Button type="submit" disabled={!$form.isValid || $form.isSubmitting}
						>Validate form</Button
					>
				</Form>
			</Card.Content></Card.Root
		>
		<div data-reveal class="flex min-w-0 flex-col gap-6">
			<Card.Root
				><Card.Header
					><Card.Title>Statuses and tables</Card.Title><Card.Description
						>Canonical status tokens, responsive cards, and shared data states.</Card.Description
					></Card.Header
				><Card.Content>
					<DataTable
						{columns}
						{data}
						{params}
						onParamsChange={(patch) => (params = { ...params, ...patch })}
						isLoading={loading}
						isError={failed}
						onRetry={() => (failed = false)}
					>
						{#snippet toolbar()}<FilterBar
								><SearchInput value={params.q} onChange={(q) => (params = { ...params, q })} />
								<div class="flex items-center gap-2">
									<Switch
										id="demo-loading"
										checked={loading}
										onCheckedChange={(/** @type {boolean} */ next) => (loading = next)}
									/><label for="demo-loading" class="text-xs">Loading</label>
								</div>
								<div class="flex items-center gap-2">
									<Switch
										id="demo-error"
										checked={failed}
										onCheckedChange={(/** @type {boolean} */ next) => (failed = next)}
									/><label for="demo-error" class="text-xs">Error</label>
								</div></FilterBar
							>{/snippet}
					</DataTable>
				</Card.Content></Card.Root
			>
			<Card.Root
				><Card.Header
					><Card.Title>One currency format</Card.Title><Card.Description
						>Server decimal strings, consistently displayed in INR.</Card.Description
					><Card.Action><Repeat2 aria-hidden="true" /></Card.Action></Card.Header
				><Card.Content><MoneyCell value="1560.00" /></Card.Content></Card.Root
			>
		</div>
	</div>
</main>
<ConfirmDialog
	open={confirmOpen}
	onOpenChange={(next) => (confirmOpen = next)}
	title="Try a confirmation"
	description="This is an example of a focused confirmation. It will not change any records."
	confirmLabel="Confirm example"
	onConfirm={() => notify.success('Confirmation complete.')}
/>
