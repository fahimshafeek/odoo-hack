<script>
	import { cn } from '#lib/utils.js';
	/** @type {any} */
	let { ref = $bindable(null), class: className, inset, children, ...restProps } = $props();
</script>

<div
	bind:this={ref}
	data-slot="dropdown-menu-label"
	data-inset={inset}
	class={cn('px-1.5 py-1 text-xs font-medium text-muted-foreground data-inset:pl-7', className)}
	{...restProps}
>
	{@render children?.()}
</div>
