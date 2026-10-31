<script>
	import { ChevronRight } from '@lucide/svelte';
	import { DropdownMenu as DropdownMenuPrimitive } from 'bits-ui';
	import { cn } from '#lib/utils.js';
	/** @type {any} */
	let { ref = $bindable(null), class: className, inset, children, ...restProps } = $props();
</script>

<DropdownMenuPrimitive.SubTrigger
	bind:ref
	data-slot="dropdown-menu-sub-trigger"
	data-inset={inset}
	class={cn(
		"flex cursor-default items-center gap-1.5 rounded-md px-1.5 py-1 text-sm outline-hidden select-none focus:bg-accent focus:text-accent-foreground not-data-[variant=destructive]:focus:**:text-accent-foreground data-inset:pl-7 data-open:bg-accent data-open:text-accent-foreground [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
		className
	)}
	{...restProps}
>
	{@render children?.()}
	<ChevronRight class="cn-rtl-flip ml-auto" />
</DropdownMenuPrimitive.SubTrigger>
