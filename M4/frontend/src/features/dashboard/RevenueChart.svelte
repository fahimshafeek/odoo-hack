<script>
	import { formatMoney } from '#lib/format.js';
	import * as Table from '#lib/components/ui/table/index.js';
	/** @type {{rows: {month: string, invoiced: string, collected: string}[]}} */
	let { rows } = $props();
	const id = $props.id();
	const height = 208;
	const width = 1000;
	// Numbers determine drawing coordinates only; financial totals remain server-owned.
	const maximum = $derived(
		Math.max(1, ...rows.flatMap((row) => [Number(row.invoiced), Number(row.collected)]))
	);
	const step = $derived(width / Math.max(rows.length, 1));
	const labelStep = $derived(Math.max(1, Math.ceil(rows.length / 6)));
	const axis = $derived(Array.from({ length: 5 }, (_, index) => (maximum * (4 - index)) / 4));
	const compactMoney = new Intl.NumberFormat('en-IN', {
		style: 'currency',
		currency: 'INR',
		notation: 'compact',
		maximumFractionDigits: 1
	});
	function monthLabel(/** @type {string} */ month, long = false) {
		return new Intl.DateTimeFormat('en-GB', {
			month: long ? 'long' : 'short',
			year: long ? 'numeric' : undefined,
			timeZone: 'UTC'
		}).format(new Date(`${month}-01T00:00:00Z`));
	}
	function barHeight(/** @type {string} */ amount) {
		return (Math.max(0, Number(amount)) / maximum) * height;
	}
</script>

<div class="flex flex-col gap-4">
	<div class="flex flex-wrap items-center gap-4 text-xs text-muted-foreground" aria-hidden="true">
		<span class="flex items-center gap-2"
			><span class="size-2.5 rounded-xs bg-foreground"></span>Collected</span
		><span class="flex items-center gap-2"
			><span class="size-2.5 rounded-xs bg-foreground/20"></span>Invoiced</span
		>
	</div>
	<div class="flex gap-3">
		<div
			class="flex h-52 w-14 shrink-0 flex-col justify-between text-right text-xs text-muted-foreground"
			aria-hidden="true"
		>
			{#each axis as amount, index (index)}<span class="leading-none"
					>{compactMoney.format(amount)}</span
				>{/each}
		</div>
		<div class="min-w-0 flex-1">
			<svg
				viewBox={`0 0 ${width} ${height}`}
				preserveAspectRatio="none"
				role="img"
				aria-labelledby={`${id}-title ${id}-description`}
				class="h-52 w-full overflow-visible"
			>
				<title id={`${id}-title`}>Monthly invoiced and collected revenue</title>
				<desc id={`${id}-description`}
					>Comparison across {rows.length} months. Exact amounts are available in the data table below.</desc
				>
				{#each axis as amount, index (index)}<line
						x1="0"
						x2={width}
						y1={height - (amount / maximum) * height}
						y2={height - (amount / maximum) * height}
						stroke="var(--border)"
						stroke-dasharray="3 3"
						vector-effect="non-scaling-stroke"
					/>{/each}
				{#each rows as row, index (row.month)}<g
						><title
							>{monthLabel(row.month, true)}: collected {formatMoney(row.collected)}, invoiced {formatMoney(
								row.invoiced
							)}</title
						><rect
							x={index * step + step * 0.18}
							y={height - barHeight(row.collected)}
							width={step * 0.28}
							height={barHeight(row.collected)}
							rx="3"
							class="fill-foreground"
						/><rect
							x={index * step + step * 0.52}
							y={height - barHeight(row.invoiced)}
							width={step * 0.28}
							height={barHeight(row.invoiced)}
							rx="3"
							class="fill-foreground/20"
						/></g
					>{/each}
			</svg>
			<div
				class="mt-3 grid text-center text-xs text-muted-foreground"
				style={`grid-template-columns: repeat(${Math.max(rows.length, 1)}, minmax(0, 1fr))`}
				aria-hidden="true"
			>
				{#each rows as row, index (row.month)}<span
						class={index % labelStep === 0 || index === rows.length - 1 ? '' : 'invisible'}
						>{monthLabel(row.month)}</span
					>{/each}
			</div>
		</div>
	</div>
	<details class="border-t pt-3">
		<summary class="w-fit cursor-pointer text-xs text-muted-foreground hover:text-foreground"
			>View data table</summary
		>
		<div class="mt-3">
			<Table.Root
				><Table.Caption class="sr-only">Monthly revenue in Indian rupees</Table.Caption
				><Table.Header
					><Table.Row
						><Table.Head>Month</Table.Head><Table.Head class="text-right">Collected</Table.Head
						><Table.Head class="text-right">Invoiced</Table.Head></Table.Row
					></Table.Header
				><Table.Body
					>{#each rows as row (row.month)}<Table.Row
							><Table.Cell>{monthLabel(row.month, true)}</Table.Cell><Table.Cell
								class="text-right tabular-nums">{formatMoney(row.collected)}</Table.Cell
							><Table.Cell class="text-right tabular-nums">{formatMoney(row.invoiced)}</Table.Cell
							></Table.Row
						>{/each}</Table.Body
				></Table.Root
			>
		</div>
	</details>
</div>
