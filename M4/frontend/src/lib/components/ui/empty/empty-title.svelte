<script>
	import { cn } from '#lib/utils.js';
	/** @type {any} */
	let { ref = $bindable(null), class: className, children, ...restProps } = $props();
</script>

<div
	bind:this={ref}
	data-slot="empty-title"
	class={cn('cn-font-heading text-sm font-medium tracking-tight', className)}
	{...restProps}
>
	{@render children?.()}
</div>
