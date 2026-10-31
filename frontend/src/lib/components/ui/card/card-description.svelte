<script>
	import { cn } from '#lib/utils.js';
	/** @type {any} */
	let { ref = $bindable(null), class: className, children, ...restProps } = $props();
</script>

<p
	bind:this={ref}
	data-slot="card-description"
	class={cn('text-sm text-muted-foreground', className)}
	{...restProps}
>
	{@render children?.()}
</p>
