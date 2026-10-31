<script>
	import { ArrowDown, ArrowUp, ChevronsUpDown, ChevronLeft, ChevronRight } from '@lucide/svelte';
	import { cn } from '#lib/utils.js';
	import * as Table from './ui/table/index.js';
	import * as Card from './ui/card/index.js';
	import * as NativeSelect from './ui/native-select/index.js';
	import { Button } from './ui/button/index.js';
	import EmptyState from './EmptyState.svelte';
	import ErrorState from './ErrorState.svelte';
	import TableSkeleton from './TableSkeleton.svelte';
	/** @typedef {Record<string, any>} Row */
	/** @typedef {{key: string, header: string, cell?: import('svelte').Snippet<[any]>, sortKey?: string, hideOnMobile?: boolean, className?: string}} Column */
	/** @type {{columns: Column[], data?: {items: Row[], total: number, page: number, page_size: number}, isLoading?: boolean, isError?: boolean, onRetry?: () => void, params: import('#lib/list-params.js').ListParams, onParamsChange: (patch: Record<string, string | number>) => void, mobileCard?: import('svelte').Snippet<[Row]>, onRowClick?: (row: Row) => void, toolbar?: import('svelte').Snippet, emptyTitle?: string, emptyDescription?: string, emptyAction?: import('svelte').Snippet}} */
	let {
		columns,
		data,
		isLoading = false,
		isError = false,
		onRetry,
		params,
		onParamsChange,
		mobileCard,
		onRowClick,
		toolbar,
		emptyTitle = 'No records found',
		emptyDescription = 'Try another search or change your filters.',
		emptyAction
	} = $props();
	const items = $derived(data?.items ?? []);
	const total = $derived(data?.total ?? 0);
	const pages = $derived(Math.max(1, Math.ceil(total / params.page_size)));
	const first = $derived(total ? (params.page - 1) * params.page_size + 1 : 0);
	const uid = $props.id();
	function sort(/** @type {string} */ key) {
		onParamsChange({ sort: params.sort === key ? `-${key}` : key });
	}
	function rowClick(/** @type {MouseEvent} */ event, /** @type {Row} */ row) {
		if (event.target instanceof Element && event.target.closest('button, a, input, select')) return;
		onRowClick?.(row);
	}
</script>

<div class="flex min-w-0 flex-col gap-4">
	{@render toolbar?.()}
	{#if isLoading}<TableSkeleton />
	{:else if isError}<ErrorState {onRetry} />
	{:else if !items.length}<EmptyState
			title={emptyTitle}
			description={emptyDescription}
			action={emptyAction}
		/>
	{:else}
		<div class="hidden overflow-hidden rounded-xl border bg-card md:block">
			<Table.Root
				><Table.Header
					><Table.Row
						>{#each columns as column (column.key)}<Table.Head
								aria-sort={column.sortKey
									? params.sort === column.sortKey
										? 'ascending'
										: params.sort === `-${column.sortKey}`
											? 'descending'
											: 'none'
									: undefined}
							>
								{#if column.sortKey}<Button
										variant="ghost"
										onclick={() => sort(column.sortKey ?? column.key)}
										>{column.header}{#if params.sort === column.sortKey}<ArrowUp
												data-icon="inline-end"
											/>{:else if params.sort === `-${column.sortKey}`}<ArrowDown
												data-icon="inline-end"
											/>{:else}<ChevronsUpDown data-icon="inline-end" />{/if}</Button
									>{:else}{column.header}{/if}
							</Table.Head>{/each}</Table.Row
					></Table.Header
				>
				<Table.Body
					>{#each items as row (row.id ?? row)}<Table.Row
							onclick={(/** @type {MouseEvent} */ event) => rowClick(event, row)}
							class={cn(onRowClick && 'cursor-pointer')}
						>
							{#each columns as column, cellIndex (column.key)}<Table.Cell class={column.className}>
									{#if cellIndex === 0 && onRowClick}<button
											type="button"
											class="text-left font-medium text-primary underline-offset-4 hover:underline"
											onclick={() => onRowClick?.(row)}
											>{#if column.cell}{@render column.cell(row)}{:else}{row[column.key] ??
													'—'}{/if}</button
										>
									{:else if column.cell}{@render column.cell(row)}{:else}{row[column.key] ??
											'—'}{/if}
								</Table.Cell>{/each}
						</Table.Row>{/each}</Table.Body
				></Table.Root
			>
		</div>
		<div class="flex flex-col gap-3 md:hidden" data-testid="mobile-records">
			{#each items as row (row.id ?? row)}
				<Card.Root
					><Card.Content>
						{#if mobileCard}{@render mobileCard(row)}{:else}<dl
								class="grid grid-cols-2 gap-x-4 gap-y-3"
							>
								{#each columns.filter((column) => !column.hideOnMobile) as column (column.key)}<dt
										class="text-xs text-muted-foreground"
									>
										{column.header}
									</dt>
									<dd class="min-w-0 text-right text-sm wrap-anywhere">
										{#if column.cell}{@render column.cell(row)}{:else}{row[column.key] ?? '—'}{/if}
									</dd>{/each}
							</dl>{/if}
						{#if onRowClick}<Button
								variant="outline"
								class="mt-4 w-full"
								onclick={() => onRowClick?.(row)}
								>View details<ChevronRight data-icon="inline-end" /></Button
							>{/if}
					</Card.Content></Card.Root
				>
			{/each}
		</div>
		<div
			class="flex flex-col gap-3 text-xs text-muted-foreground sm:flex-row sm:items-center sm:justify-between"
		>
			<p aria-live="polite">
				Showing {first}–{Math.min(first + items.length - 1, total)} of {total} records
			</p>
			<div class="flex flex-wrap items-center gap-3">
				<label for={`${uid}-page-size`}>Rows per page</label><NativeSelect.Root
					id={`${uid}-page-size`}
					value={String(params.page_size)}
					onchange={(/** @type {Event} */ event) =>
						onParamsChange({
							page_size: Number(/** @type {HTMLSelectElement} */ (event.currentTarget).value)
						})}
				>
					{#each [10, 25, 50, 100] as size (size)}<NativeSelect.Option value={String(size)}
							>{size}</NativeSelect.Option
						>{/each}
				</NativeSelect.Root>
				<nav aria-label="Pagination" class="flex items-center gap-2">
					<Button
						variant="outline"
						size="icon"
						aria-label="Previous page"
						disabled={params.page <= 1}
						onclick={() => onParamsChange({ page: params.page - 1 })}><ChevronLeft /></Button
					><span>Page {params.page} of {pages}</span><Button
						variant="outline"
						size="icon"
						aria-label="Next page"
						disabled={params.page >= pages}
						onclick={() => onParamsChange({ page: params.page + 1 })}><ChevronRight /></Button
					>
				</nav>
			</div>
		</div>
	{/if}
</div>
