<script>
	import { Calendar } from 'bits-ui';
	import { parseDate } from '@internationalized/date';
	import { CalendarDays, ChevronLeft, ChevronRight } from '@lucide/svelte';
	import * as Popover from './ui/popover/index.js';
	import { Button } from './ui/button/index.js';
	/** @type {{value?: string, onChange: (value: string) => void, id?: string, label?: string, disabled?: boolean, min?: string | number, max?: string | number, invalid?: boolean, describedBy?: string}} */
	let {
		value = '',
		onChange,
		id,
		label = 'Select date',
		disabled = false,
		min,
		max,
		invalid,
		describedBy
	} = $props();
	let open = $state(false);
	function date(/** @type {string | number | undefined} */ input) {
		try {
			return input ? parseDate(String(input)) : undefined;
		} catch {
			return undefined;
		}
	}
	const selected = $derived(date(value));
	const display = $derived(
		selected
			? new Intl.DateTimeFormat('en-IN', {
					day: 'numeric',
					month: 'short',
					year: 'numeric'
				}).format(selected.toDate('Asia/Kolkata'))
			: label
	);
</script>

<Popover.Root bind:open>
	<Popover.Trigger>
		{#snippet child({ props })}
			<Button
				{...props}
				{id}
				{disabled}
				variant="outline"
				class="w-full justify-between"
				aria-label={label}
				aria-invalid={invalid}
				aria-describedby={describedBy}
			>
				{display}<CalendarDays data-icon="inline-end" />
			</Button>
		{/snippet}
	</Popover.Trigger>
	<Popover.Content align="start" class="w-auto p-3">
		<Calendar.Root
			type="single"
			value={selected}
			minValue={date(min)}
			maxValue={date(max)}
			locale="en-IN"
			weekdayFormat="short"
			fixedWeeks
			onValueChange={(next) => {
				onChange(next?.toString() ?? '');
				if (next) open = false;
			}}
		>
			{#snippet children({ months, weekdays })}
				<Calendar.Header class="mb-3 flex items-center justify-between gap-2">
					<Calendar.PrevButton
						class="flex size-9 items-center justify-center rounded-md border hover:bg-muted disabled:opacity-40"
						><ChevronLeft class="size-4" /></Calendar.PrevButton
					>
					<Calendar.Heading class="sr-only" />
					<div class="flex items-center gap-1">
						<Calendar.MonthSelect
							class="h-9 rounded-md border bg-background px-2 text-sm"
						/><Calendar.YearSelect class="h-9 rounded-md border bg-background px-2 text-sm" />
					</div>
					<Calendar.NextButton
						class="flex size-9 items-center justify-center rounded-md border hover:bg-muted disabled:opacity-40"
						><ChevronRight class="size-4" /></Calendar.NextButton
					>
				</Calendar.Header>
				{#each months as month (month.value.toString())}
					<Calendar.Grid class="border-collapse">
						<Calendar.GridHead
							><Calendar.GridRow
								>{#each weekdays as day (day)}<Calendar.HeadCell
										class="size-9 text-xs font-normal text-muted-foreground"
										>{day.slice(0, 2)}</Calendar.HeadCell
									>{/each}</Calendar.GridRow
							></Calendar.GridHead
						>
						<Calendar.GridBody
							>{#each month.weeks as week, index (index)}<Calendar.GridRow
									>{#each week as day (day.toString())}<Calendar.Cell
											date={day}
											month={month.value}
											class="p-0"
											><Calendar.Day
												class="size-9 rounded-md text-sm hover:bg-muted data-disabled:pointer-events-none data-disabled:opacity-30 data-outside-month:text-muted-foreground data-selected:bg-primary data-selected:text-primary-foreground data-today:underline"
												>{day.day}</Calendar.Day
											></Calendar.Cell
										>{/each}</Calendar.GridRow
								>{/each}</Calendar.GridBody
						>
					</Calendar.Grid>
				{/each}
			{/snippet}
		</Calendar.Root>
		<div class="mt-3 flex justify-end border-t pt-2">
			<Button
				variant="ghost"
				size="sm"
				onclick={() => {
					onChange('');
					open = false;
				}}>Clear date</Button
			>
		</div>
	</Popover.Content>
</Popover.Root>
