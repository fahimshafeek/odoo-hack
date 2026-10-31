<script>
	import { UserPlus } from '@lucide/svelte';
	import { createListQuery } from '#src/api/resources.js';
	import { useListParams } from '#lib/use-list-params.js';
	import { reveal } from '#lib/motion/reveal.js';
	import { PageHeader, DataTable, FilterBar, SearchInput } from '#lib/components/index.js';
	import { Button } from '#lib/components/ui/button/index.js';
	import { Badge } from '#lib/components/ui/badge/index.js';
	import StaffDialog from './StaffDialog.svelte';
	const list = useListParams();
	const staff = createListQuery('staff', '/staff', () => list.value);
	let dialog = $state(false);
	/** @type {any} */ let selected = $state(null);
	const columns = [
		{ key: 'full_name', header: 'Name' },
		{ key: 'email', header: 'Email' },
		{ key: 'is_active', header: 'Status', cell: statusCell },
		{ key: 'actions', header: '', cell: actionCell }
	];
	function edit(/** @type {any} */ row) {
		selected = row;
		dialog = true;
	}
</script>

<svelte:head><title>Staff · Brightloop</title></svelte:head>
{#snippet statusCell(row = /** @type {any} */ ({}))}<Badge
		variant={row.is_active ? 'secondary' : 'outline'}>{row.is_active ? 'Active' : 'Inactive'}</Badge
	>{/snippet}
{#snippet actionCell(row = /** @type {any} */ ({}))}<Button
		variant="ghost"
		size="sm"
		onclick={() => edit(row)}
		aria-label={`Edit ${row.full_name}`}>Edit</Button
	>{/snippet}
<main id="main-content" class="flex flex-col gap-4" {@attach reveal}>
	<div data-reveal>
		<PageHeader title="Staff" subtitle="Manage staff accounts and access."
			>{#snippet primaryAction()}<Button
					onclick={() => {
						selected = null;
						dialog = true;
					}}><UserPlus data-icon="inline-start" />Invite staff</Button
				>{/snippet}</PageHeader
		>
	</div>
	<div data-reveal>
		<DataTable
			{columns}
			data={$staff.data}
			isLoading={$staff.isPending}
			isError={$staff.isError}
			onRetry={() => void $staff.refetch()}
			params={list.value}
			onParamsChange={list.update}
			emptyTitle="No staff accounts"
			emptyDescription="Invite a team member to give them staff access."
			>{#snippet toolbar()}<FilterBar
					><SearchInput
						value={list.value.q}
						onChange={(q) => list.update({ q })}
						placeholder="Search staff…"
					/></FilterBar
				>{/snippet}{#snippet mobileCard(row)}<div class="flex flex-col gap-3">
					<div class="flex items-center justify-between gap-3">
						<p class="font-medium">{row.full_name}</p>
						<Badge variant={row.is_active ? 'secondary' : 'outline'}
							>{row.is_active ? 'Active' : 'Inactive'}</Badge
						>
					</div>
					<p class="text-sm text-muted-foreground">{row.email}</p>
					<Button variant="outline" size="sm" onclick={() => edit(row)}>Edit account</Button>
				</div>{/snippet}</DataTable
		>
	</div>
</main>
{#if dialog}<StaffDialog staff={selected} onClose={() => (dialog = false)} />{/if}
